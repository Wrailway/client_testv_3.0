## 测试所有电机的工作电流
import datetime
import logging
import concurrent.futures
import os
import re
import sys
import time
from typing import List, Tuple
import logging

from OHandSerialAPI import HAND_RESP_SUCCESS, HAND_PROTOCOL_UART, MAX_MOTOR_CNT, MAX_THUMB_ROOT_POS, MAX_FORCE_ENTRIES, OHandSerialAPI
from can_interface import *

# 设置日志级别为INFO，获取日志记录器实例
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 检查log文件夹是否存在，如果不存在则创建
log_folder = "./log"
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
    
# 获取当前时间的时间戳（精确到秒）
timestamp = str(int(time.time()))
# 获取当前日期，格式为年-月-日
current_date = time.strftime("%Y-%m-%d", time.localtime())
# 构建完整的文件名，包含路径、日期和时间戳
log_file_name = f'./log/MotorCurrentTest_log_{current_date}_{timestamp}.txt'

# 创建一个文件处理器，用于将日志写入文件
file_handler = logging.FileHandler(log_file_name)
file_handler.setLevel(logging.INFO)

# 创建一个日志格式
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)

# 将文件处理器添加到日志记录器
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(stream_handler)

class MotorCurrentTest:
    def __init__(self):
        self.node_id = 2
        self.port = 'PCAN_USBBUS1'
        self.ADDRESS_MASTER = 0x01
        self.can_interface_instance = None
        self.serial_api_instance = None
        self.DELAY_MS = 200
        # self.DELAY_MS_FUN = 6000
        self.POS_MAX_LOSS = 200
        self.DEFAULT_SPEED = 100
        self.SIXTH_FINGER_MIN_POS = 728
        self.max_average_times = 5
        self.initial_gesture = [[0,0,0,0,0,728],[0,0,0,0,0,728]] #自然展开2°对应的值1456
        self.thumb_up_gesture = [[0,0,0,0,0,728],[0, 65535, 65535, 65535, 65535, 728]] # 四指弯曲
        self.thumb_bend_gesture = [[0,0,0,0,0,728],[65535, 0, 0, 0, 0, 728]] # 大拇值弯曲
        self.thumb_rotation_gesture = [[0,0,0,0,0,728],[0, 0, 0, 0, 0, 65535]] # 大拇指旋转到对掌位

        self.gestures = self.create_gesture_dict()
        self.collectMotorCurrents = {
            'thumb':[0.0,0.0],
            'index':[0.0,0.0],
            'middle':[0.0,0.0],
            'third':[0.0,0.0],
            'little':[0.0,0.0],
            'thumb_root':[0.0,0.0]
        }
        
        self.start_motor_currents =[0.0,0.0,0.0,0.0,0.0,0.0]
        self.end_motor_currents =[0.0,0.0,0.0,0.0,0.0,0.0]
        
    def set_port(self,port):
        self.port = port
        
    def set_node_id(self,node_id=2):
        self.node_id = node_id
        
    def create_gesture_dict(self):
        gesture_dict = {
            '大拇值弯曲': self.thumb_bend_gesture,
            '大拇指旋转到对掌位': self.thumb_rotation_gesture,
             '四指弯曲': self.thumb_up_gesture,
             '自然展开': self.initial_gesture
        }
        return gesture_dict
    
    
    def checkCurrent(self, curs):
        """
        检查电机电流是否超过100mA。

        遍历输入的电流列表，如果有任何一个电流值大于100则返回False，否则返回True。

        :param curs: 一个包含电机电流值的列表。
        :return: 一个布尔值，表示电流是否都在正常范围内。
        """
        return all(c <= 100 for c in curs)
    
    def connect_device(self):
        connect_status = True
        try:
            port_num = port_num = int(re.findall(r'\d+', self.port)[0])
            self.can_interface_instance = CAN_Init(port_name=port_num, baudrate=1000000)
            if self.can_interface_instance is None:
                connect_status = False
                logger.info("port init failed\n")
            protocol = HAND_PROTOCOL_UART
            self.serial_api_instance = OHandSerialAPI(self.can_interface_instance, protocol, self.ADDRESS_MASTER,
                                                    send_data_impl,
                                                    recv_data_impl)
            self.serial_api_instance.HAND_SetTimerFunction(get_milli_seconds_impl, delay_milli_seconds_impl)
            self.serial_api_instance.HAND_SetCommandTimeOut(255)
        except Exception as e:
            logger.info(f"\n初始化异常: {str(e)}")
            connect_status = False
        return connect_status

    def disConnect_device(self):
        if self.serial_api_instance and hasattr(self.serial_api_instance, "shutdown"):  # 检查是否有自定义关闭方法
            try:
                self.serial_api_instance.shutdown()
                self.serial_api_instance = None
                logger.info("API shutdown successfully")
                
            except Exception as e:
                logger.error(f"Error during API shutdown: {e}")

        if self.can_interface_instance and hasattr(self.can_interface_instance, "shutdown"):
            try:
                self.can_interface_instance.shutdown()
                self.can_interface_instance = None
                logger.info("CAN bus connection closed")
            except Exception as e:
                logger.error(f"Error closing CAN bus: {e}")

    def do_gesture(self, gesture):
        """
        执行特定的手势动作。

        实际是向特定寄存器（ROH_FINGER_POS_TARGET0）写入手势数据。

        :param gesture: 要执行的手势数据。
        :return: 调用write_to_regesister方法的结果，即写入是否成功的布尔值。
        """
        return self.write_to_regesister(address=self.ROH_FINGER_POS_TARGET0, value=gesture[0]) and self.write_to_regesister(address=self.ROH_FINGER_POS_TARGET0, value=gesture[1]) 
    
    def do_gesture(self, gesture):
        result = True
        for ges in gesture:
            delay_milli_seconds_impl(self.DELAY_MS*5)
            for finger_id in range(MAX_MOTOR_CNT):
                remote_err = []
                # delay_milli_seconds_impl(self.DELAY_MS)
                err = self.serial_api_instance.HAND_SetFingerPos(
                        self.node_id, finger_id, 
                        ges[finger_id],          # 测试变量位置值
                        self.DEFAULT_SPEED,  # 速度固定为默认值
                        remote_err
                    )
                if err != HAND_RESP_SUCCESS:
                    result = False
                    break
        return result
    
    def count_motor_curtent(self):
        """
        计算各电机电流限制的平均值
        返回：各手指（MAX_MOTOR_CNT个）的电流限制平均值列表
        """
        sum_currents = [0.0] * MAX_MOTOR_CNT  # 用float避免整数除法精度丢失
        average_times = self.max_average_times if self.max_average_times > 0 else 1  # 防止除以0
        delay_milli_seconds_impl(self.DELAY_MS*10)
        # 循环采集电流限制值并累加
        for i in range(average_times):
            for finger_id in range(MAX_MOTOR_CNT):
                delay_milli_seconds_impl(self.DELAY_MS)  # 缩短采集间隔
                current_limit = [0]
                err, current_limit_get = self.serial_api_instance.HAND_GetFingerCurrent(
                    self.node_id,
                    finger_id,
                    current_limit,
                    []
                )
                # 仅当采集成功时累加（排除错误数据）
                if err == HAND_RESP_SUCCESS:
                    # 兼容current_limit_get是列表/单个值的情况
                    current_val = current_limit_get[0] if isinstance(current_limit_get, list) else current_limit_get
                    sum_currents[finger_id] += current_val
                else:
                    logger.warning(f"端口{self.port} 手指{finger_id} 第{i+1}次采集电流失败，错误码:{err}")

        # 计算平均值（逐手指除法）
        motor_currents = [sum_val / average_times for sum_val in sum_currents]
        logger.info(f"端口{self.port} 电机电流平均值: {motor_currents}")
        return motor_currents
        
    def collect_start_and_end_currents(self,ges='',current=[]):
        if ges == '自然展开':
            self.start_motor_currents = current
        elif ges == '四指弯曲':
            self.end_motor_currents[1:4] = current[1:4]
        elif ges == '大拇值弯曲':
            self.end_motor_currents[0] = current[0]
        elif ges == '大拇指旋转到对掌位':
            self.end_motor_currents[5] = current[5]
        else:
            logger.error('错误的手势')
            
    def collect_motor_currents(self):
        for key in self.collectMotorCurrents:
            index = list(self.collectMotorCurrents.keys()).index(key)
            self.collectMotorCurrents[key][0] = self.start_motor_currents[index]
            self.collectMotorCurrents[key][1] = self.end_motor_currents[index]
        
        # logger.info(f'port = {self.port}\n')
        print(*[f"[port = {self.port}][{key}]电机电流-->  <start> {values[0]}ma, <end> {values[1]}ma\n" for key, values in self.collectMotorCurrents.items()], sep='\n')

test_title = '电机电流测试\n标准：电流值范围 < 0~100mA >'
expected = [100, 100, 100, 100, 100, 100]
description = '各个手指在始末位置,记录各个电机的电流值'


def main(ports: list = [], node_ids: list = [], aging_duration: float = 0) -> Tuple[str, List, str, bool]:
    """
    测试的主函数。

    创建 AgeTest 类的实例，设置端口号并连接设备，然后进行多次（最多 aging_duration 次）测试循环，
    在每次循环中获取电机电流并检查电流是否正常，根据结果设置 result 变量，最后断开设备连接并返回测试结果。

    :param ports: 要连接的设备端口号列表，默认为空列表。
    :param node_ids: 与端口号对应的设备节点ID列表，默认为空列表。
    :param aging_duration: 测试持续时长，默认为1，单位根据具体业务逻辑确定（可能是小时等）。
    :return: 包含测试标题、整体测试结果、最终测试结论、是否显示电流的元组。
    """
    overall_result = []
    final_result = '通过'
    need_show_current = True

    start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f'---------------------------------------------开始测试电机电流<开始时间：{start_time}>----------------------------------------------\n')
    logger.info('测试目的：各个手指在始末位置，各个电机的电流表现')
    logger.info('标准：电流值范围 < 0~100mA >\n')
    try:
        logger.info(f"##########################测试开始######################\n")
        with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
            futures = [executor.submit(test_single_port, port, node_id, False) for port, node_id in zip(ports, node_ids)]
            for future in concurrent.futures.as_completed(futures):
                port_result, _ = future.result()
                overall_result.append(port_result)
                for gesture_result in port_result["gestures"]:
                    if gesture_result["result"]!= "通过":
                        final_result = '不通过'
                        break
        logger.info(f"#################测试结束，测试结果：{final_result}#############\n")
    except concurrent.futures.TimeoutError:
        logger.error("测试超时异常，部分任务未能按时完成")
        final_result = '不通过'
    except ConnectionError as conn_err:
        logger.error(f"设备连接出现问题：{conn_err}")
        final_result = '不通过'
    except Exception as e:
        logger.exception("未知异常发生，测试出现错误")
        final_result = '不通过'
    # finally:
    #     # 可以在这里添加一些通用的资源清理操作，比如关闭文件句柄（若有相关操作）、释放临时占用的资源等
    #     logger.info("执行测试结束后的清理操作（如有）")
    end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f'---------------------------------------------电机电流测试结束<结束时间：{end_time}>----------------------------------------------\n')
    return test_title, overall_result, need_show_current

def build_gesture_result(timestamp, result, motors_current):
    """
    根据给定的时间戳、测试结果以及电机电流值构建手势结果字典。
    """
    return {
        "timestamp": timestamp,
        "description": description,
        "expected": expected,
        "content": motors_current,
        "result": result,
        "comment": '无'
    }


def test_single_port(port, node_id, connected_status):
    result = '通过'
    motor_current_test = MotorCurrentTest()
    motor_current_test.set_port(port=port)
    motor_current_test.set_node_id(node_id=node_id)
    
    connected_status = motor_current_test.connect_device()
    
    port_result = {
        "port": port,
        "gestures": []
    }
    
    if connected_status:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            for gesture_name, gesture in motor_current_test.gestures.items():
                if motor_current_test.do_gesture(gesture=gesture):
                    logger.info(f'[port = {port}]执行    ---->  {gesture_name}')
                    time.sleep(5)
                    motors_current = motor_current_test.count_motor_curtent()
                    logger.info(f'[port = {port}]电机电流为 -->{motors_current}')
                    if  not motor_current_test.checkCurrent(motors_current):
                        result = '不通过'
                motor_current_test.collect_start_and_end_currents(ges=gesture_name, current=motors_current)
            motor_current_test.collect_motor_currents()
            gesture_result = build_gesture_result(timestamp, result, motor_current_test.collectMotorCurrents)
            port_result["gestures"].append(gesture_result)
        except Exception as current_error:
            logger.error(f"获取电机电流或检查电流时出现错误：{current_error}")
            result = '不通过'
            gesture_result = build_gesture_result(timestamp, result, [])
            port_result["gestures"].append(gesture_result)
        finally:
            motor_current_test.disConnect_device()
    return port_result, connected_status
            
if __name__ == "__main__":
    ports = ['PCAN_USBBUS1']
    node_ids = [2]
    main(ports = ports,node_ids = node_ids,aging_duration=1)