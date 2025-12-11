import datetime
import json
import logging
import concurrent.futures
import os
import re
import sys
import time
from typing import List, Optional, Tuple
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
log_file_name = f'./log/AgingTest_log_{current_date}_{timestamp}.txt'

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

fail_port_list = set()
class AgingTest:
    
    def __init__(self):
        """
        初始化AgeTest类的实例。

        在这里设置与Modbus设备通信相关的参数，包括端口号、节点ID、帧类型、波特率等，
        同时定义了与手指位置和电机电流相关的寄存器地址、初始手势、握手势、最大循环次数等属性。
        """
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
    
        self.motor_currents = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.initial_gesture = [[26069, 31499, 36569, 32949, 28966, 62258],[0, 0, 0, 0, 0, 62258]]  # 自然展开手势
        self.grasp_gesture = [[0,  31499, 36569, 32949, 28966, 62258], [26069, 31499, 36569, 32949, 28966, 62258]]
        self.FINGER_POS_TARGET_MAX_LOSS = 32
        self.max_average_times = 3
        self.current_standard = 100
        
    def do_gesture(self, gesture):
        for finger_id in range(MAX_MOTOR_CNT):
            remote_err = []
            err = self.serial_api_instance.HAND_SetFingerPos(
                    self.node_id, finger_id, 
                    gesture[finger_id],          # 测试变量位置值
                    self.DEFAULT_SPEED,  # 速度固定为默认值
                    remote_err
                )
        return err == HAND_RESP_SUCCESS
    
    def count_motor_curtent(self):
        """
        计算各电机电流限制的平均值
        返回：各手指（MAX_MOTOR_CNT个）的电流限制平均值列表
        """
        sum_currents = [0.0] * MAX_MOTOR_CNT  # 用float避免整数除法精度丢失
        average_times = self.max_average_times if self.max_average_times > 0 else 1  # 防止除以0
        delay_milli_seconds_impl(self.DELAY_MS*5)
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

         # 计算平均值 + 四舍五入保留三位小数（核心修改）
        self.motor_currents = [round(sum_val / average_times, 3) for sum_val in sum_currents]
        
        # 日志输出（格式统一）
        # formatted_currents = [f"{c:.3f}" for c in self.motor_currents]
        # logger.info(f"端口{self.port} 电机电流平均值: [{', '.join(formatted_currents)}] mA")
        return self.motor_currents
                
    def check_current(self, curs):
        """
        检查电机电流是否超过标准<100mA>
        :param curs: 一个包含电机电流值的列表。
        :return: 一个布尔值，表示电流是否都在正常范围内。
        """
        return all(c <= self.current_standard for c in curs)
    
    def set_max_current(self):
        value = [200]*MAX_MOTOR_CNT
        for finger_id in range(MAX_MOTOR_CNT):
            remote_err = []
            delay_milli_seconds_impl(self.DELAY_MS*5)
            err = self.serial_api_instance.HAND_SetFingerCurrentLimit(
                    self.node_id, finger_id, 
                    value[finger_id], 
                    remote_err
                )
            delay_milli_seconds_impl(self.DELAY_MS)
            return  err == HAND_RESP_SUCCESS

    def get_HAND_FingerPos(self,serial_api_instance,finger_id):
        # delay_milli_seconds_impl(self.DELAY_MS)
        target_pos = [0]
        current_pos = [0]
        return serial_api_instance.HAND_GetFingerPos(self.node_id, finger_id, target_pos, current_pos, [])

    def judge_if_hand_broken(self, gesture):
        """
        判断设备是否损坏。

        通过读取指定地址的寄存器数据，并与给定的手势数据对比，如果有任何一个寄存器值与手势值的差值超过FINGER_POS_TARGET_MAX_LOSS则认为设备损坏。

        :param address: 要读取数据的寄存器地址。
        :param gesture: 用于对比的手势数据。
        :return: 一个布尔值，表示设备是否损坏。
        """
        delay_milli_seconds_impl(self.DELAY_MS*6)
        is_broken = False
        for finger_id in range(MAX_MOTOR_CNT):
            # delay_milli_seconds_impl(self.DELAY_MS)
            value = self.get_HAND_FingerPos(self.serial_api_instance,finger_id)
            if value[0] == HAND_RESP_SUCCESS:
                if finger_id == MAX_MOTOR_CNT-1:
                    # 第六指特殊逻辑：写入<728时，读取值应为728；否则校验与写入值一致
                    if gesture[finger_id] < self.SIXTH_FINGER_MIN_POS:
                        if value[2] == self.SIXTH_FINGER_MIN_POS:
                            continue
                        else:
                            is_broken = True
                            break
                    else:
                        if abs(value[2] - gesture[finger_id]) < self.POS_MAX_LOSS:
                            continue
                        else:
                            is_broken = True
                            break
                else:
                        # 其他手指：常规容差校验
                        if abs(value[2] - gesture[finger_id]) <self.POS_MAX_LOSS:
                            continue
                        else:
                            is_broken = True
                            break
            else:
                is_broken = False
        return is_broken
                                

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

def read_from_json_file():
        """
        从json文件读取标志位，判断是否继续执行测试
        Returns:
            返回fasle则终止测试，true继续测试
        """
        try:
            with open('shared_data.json', 'r') as f:
                data = json.load(f)
                stop_test = data['stop_test']
                pause_test = data['pause_test']
                return stop_test,pause_test
        except FileNotFoundError:
            # logger.error("共享的json文件不存在")
            return False,False
        except json.JSONDecodeError:
            # logger.error("json文件数据格式错误")
            return False,False
        except Exception as e:
            # logger.error(f"读取JSON文件时出现其他未知错误: {e}")
            return False, False

test_title = '老化测试报告\n标准：各个手头无异常，手指不脱线，并记录各个电机的电流值 < 单位 mA >'
expected = [100, 100, 100, 100, 100, 100]
description = '重复抓握手势,记录各个电机的电流值'  # 用例描述

# 定义一个常量用于表示老化测试的时长单位转换（从小时转换为秒）
SECONDS_PER_HOUR = 3600

def check_port(valid_port: set = {}, total_port: list = {}, node_ids: list = []):
    """
    从total_port列表中去除valid_port集合中的元素，并同步去除对应的node_ids列表中的元素，
    基于total_port中的端口和node_ids中的元素按位置一一对应关系。

    参数:
    valid_port (set): 要去除的端口集合，默认为空集合。
    total_port (list): 总的端口列表，默认为空列表。
    node_ids (list): 与total_port中的端口对应的节点标识列表，默认为空列表。

    返回:
    list: 去除指定端口后的端口列表。
    list: 去除对应端口后对应的节点标识列表。
    """
    # 检查参数类型是否符合要求
    if not isinstance(valid_port, set):
        raise TypeError("valid_port参数应该是set类型")
    if not isinstance(total_port, list):
        raise TypeError("total_port参数应该是list类型")
    if not isinstance(node_ids, list):
        raise TypeError("node_ids参数应该是list类型")

    # 使用列表推导式从total_port中筛选出不在valid_port中的元素，同时记录符合条件的索引位置
    valid_indices = [index for index, port in enumerate(total_port) if port not in valid_port]
    # 根据记录的有效索引位置，从node_ids列表中筛选出对应的元素，构建新的node_ids列表
    result_node_ids = [node_ids[i] for i in valid_indices]
    # 使用筛选出的有效索引位置，从total_port列表中构建新的端口列表
    result_ports = [total_port[i] for i in valid_indices]
    return result_ports, result_node_ids

def main(ports: list = [], node_ids: list = [], aging_duration: float = 1.5) -> Tuple[str, List, str, bool]:
    """
    测试的主函数。
    :param ports: 端口列表
    :param node_ids: 设备id列表,与端口号一一对应
    :return: 测试标题,测试结果数据,测试结论,是否需要显示电机电流(false)
    """
    overall_result = []
    final_result = '通过'
    start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f'---------------------------------------------开始老化测试<开始时间：{start_time}>----------------------------------------------\n')
    logger.info('测试目的：循环做抓握手势，进行压测')
    logger.info('标准：各个手头无异常，手指不脱线，并记录各个电机的电流值 < 单位 mA >\n')
    try:
        end_time = time.time() + aging_duration * SECONDS_PER_HOUR
        round_num = 0
        while time.time() < end_time:
            ports,node_ids = check_port(valid_port=fail_port_list,total_port=ports,node_ids=node_ids)
            if len(ports)==0:
                logger.info('无可测试设备')
                break
            round_num += 1
            logger.info(f"##########################第 {round_num} 轮测试开始######################\n")
            result = '通过'
            stop_test,pause_test = read_from_json_file()
            if stop_test:
                logger.info('测试已停止')
                break
                
            if pause_test:
                logger.info('测试暂停')
                time.sleep(2)
                continue

            round_results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
                futures = [executor.submit(test_single_port, port, node_id) for port, node_id in zip(ports, node_ids)]
                for future in concurrent.futures.as_completed(futures):
                    port_result, _ = future.result()
                    round_results.append(port_result)
                    for gesture_result in port_result["gestures"]:
                        if gesture_result["result"]!= "通过":
                            result = '不通过'
                            final_result = '不通过'
                            break
            overall_result.extend(round_results)
            
            logger.info(f"#################第 {round_num} 轮测试结束，测试结果：{result}#############\n")
    except Exception as e:
        final_result = '不通过'
        logger.error(f"Error: {e}")
    # finally:
    #     logger.info("执行测试结束后的清理操作（如有）")
    end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f'---------------------------------------------老化测试结束，测试结果：{final_result}<结束时间：{end_time}>----------------------------------------------\n')
    print_overall_result(overall_result)
    return test_title, overall_result, False

def test_single_port(port, node_id):
    """
    针对单个端口进行测试，返回该端口测试结果的字典，包含端口号、是否通过及具体手势测试结果等信息。
    """
    aging_test = AgingTest()
    aging_test.port = port
    aging_test.node_id = node_id
    
    connected_status = aging_test.connect_device()
    
    port_result = {
        'port': port,
        'gestures': []
    }
    
    if connected_status:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        grasp_gesture = aging_test.grasp_gesture
        initial_gesture = aging_test.initial_gesture
        try:
            if aging_test.set_max_current(): # 设置最大的电量限制为200ma
                if aging_test.do_gesture(grasp_gesture[0]) and aging_test.do_gesture(grasp_gesture[1]):
                    aging_test.count_motor_curtent()
                    logger.info(f'[port = {port}]执行抓握手势，电机电流为 -->{aging_test.motor_currents}\n')
                if aging_test.do_gesture(initial_gesture[0]) and aging_test.do_gesture(initial_gesture[1]):
                    if not aging_test.judge_if_hand_broken(initial_gesture[1]):
                        motor_currents = aging_test.motor_currents
                        if aging_test.check_current(motor_currents):
                            gesture_result = build_gesture_result(timestamp =timestamp,content=motor_currents,result='通过',comment='无')
                        else:
                            gesture_result = build_gesture_result(timestamp =timestamp,content=motor_currents,result='不通过',comment='电流超标')
                        gesture_result = build_gesture_result(timestamp =timestamp,content=motor_currents,result='通过',comment='无')
                    else:
                        gesture_result = build_gesture_result(timestamp =timestamp,content='',result='不通过',comment='手指出现异常')
                else:
                    gesture_result = build_gesture_result(timestamp =timestamp,content='',result='不通过',comment='手指出现异常')
            else:
                gesture_result = build_gesture_result(timestamp =timestamp,content='',result='不通过',comment='设置手指最大电流失败')
                    
            port_result['gestures'].append(gesture_result)
        except Exception as e:
            error_gesture_result = build_gesture_result(timestamp =timestamp,content='',result='不通过',comment=f'出现错误：{e}')
            port_result['gestures'].append(error_gesture_result)
        finally:
            aging_test.disConnect_device()
    return port_result,connected_status

def build_gesture_result(timestamp,content,result,comment):
    return {
            "timestamp": timestamp,
            "description": description,
            "expected": expected,
            "content": content,
            "result": result,
            "comment": comment
        }
def print_overall_result(overall_result):
        port_data_dict = {}

        # 整理数据
        for item in overall_result:
            if item['port'] not in port_data_dict:
                port_data_dict[item['port']] = []
            for gesture in item['gestures']:
                port_data_dict[item['port']].append((gesture['timestamp'],gesture['description'],gesture['expected'],gesture['content'], gesture['result'], gesture['comment']))

        # 打印数据
        for port, data_list in port_data_dict.items():
            logger.info(f"Port: {port}")
            for timestamp, description, expected, content, result, comment in data_list:
                logger.info(f" timestamp:{timestamp} ,description:{description},expected:{expected},content: {content}, Result: {result},comment:{comment}")
                
if __name__ == "__main__":
    ports = ['PCAN_USBBUS1']
    node_ids = [2]
    aging_duration = 0.02
    main(ports = ports, node_ids = node_ids, aging_duration = aging_duration)