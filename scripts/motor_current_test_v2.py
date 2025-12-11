## 测试所有电机的工作电流
import datetime
import logging
import concurrent.futures
import os
import sys
import time
from typing import List, Tuple
import logging

from pymodbus.exceptions import ConnectionException
from pymodbus import FramerType
from pymodbus.client import ModbusSerialClient

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
        self.port = 'COM4'
        self.FRAMER_TYPE = FramerType.RTU
        self.BAUDRATE = 115200
        self.client = None
        self.ROH_FINGER_POS_TARGET0 = 1135
        self.ROH_FINGER_CURRENT0 = 1105
        self.ROH_BEEP_PERIOD  = 1010
        self.max_average_times = 5
        self.initial_gesture = [[0,0,0,0,0,0],[0,0,0,0,0,0]] #自然展开2°对应的值1456
        self.thumb_up_gesture = [[0,0,0,0,0,0],[0, 65535, 65535, 65535, 65535, 0]] # 四指弯曲
        self.thumb_bend_gesture = [[0,0,0,0,0,0],[65535, 0, 0, 0, 0, 0]] # 大拇值弯曲
        self.thumb_rotation_gesture = [[0,0,0,0,0,0],[0, 0, 0, 0, 0, 65535]] # 大拇指旋转到对掌位

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
    
    def read_from_register(self, address, count):
        """
        从指定的寄存器地址读取数据。
        :param address: 要读取的寄存器地址。
        :param count: 要读取的寄存器数量。
        :return: 如果成功读取则返回pymodbus的read_holding_registers响应对象，否则返回None。
        """
        try:
            response = self.client.read_holding_registers(address=address, count=count, slave=self.node_id)
            if response.isError():
                error_type = self.get_exception(response)
                logger.error(f'[port = {self.port}]读寄存器失败: {error_type}\n')
        except Exception as e:
            logger.error(f'[port = {self.port}]异常: {e}')
        return response
        
    def write_to_regesister(self, address, value):
        """
        向指定的寄存器地址写入数据。
        :param address: 要写入的寄存器地址。
        :param value: 要写入的值。
        :return: 如果写入成功则返回True，否则返回False。
        """
        try:
            response = self.client.write_registers(address, value, self.node_id)
            if not response.isError():
                    return True
            else:
                error_type = self.get_exception(response)
                logger.error(f'[port = {self.port}]写寄存器失败: {error_type}\n')
                return False
        except Exception as e:
                logger.error(f'[port = {self.port}]异常: {e}')
                return False
    
    def checkCurrent(self, curs):
        """
        检查电机电流是否超过100mA。

        遍历输入的电流列表，如果有任何一个电流值大于100则返回False，否则返回True。

        :param curs: 一个包含电机电流值的列表。
        :return: 一个布尔值，表示电流是否都在正常范围内。
        """
        return all(c <= 100 for c in curs)
    
    def connect_device(self):
        """
        连接到Modbus设备。

        创建ModbusSerialClient实例并尝试连接到指定端口的设备，根据连接结果记录日志并返回连接是否成功的布尔值。

        :return: 一个布尔值，表示是否成功连接到设备。
        """
        connect_status = False
        try:
            self.client = ModbusSerialClient(port=self.port, framer=self.FRAMER_TYPE, baudrate=self.BAUDRATE)
            connect_status = self.client.connect()
            logger.info(f"[port = {self.port}]Successfully connected to Modbus device.")
        except ConnectionException as e:
            logger.error(f"[port = {self.port}]Error during setup: {e}")
        except Exception as e:
            logger.error(f"[port = {self.port}]Error during setup: {e}")
        return connect_status

    def disConnect_device(self):
        """
        断开与Modbus设备的连接。

        如果存在client实例则关闭连接并将client设置为None，同时记录日志，如果出现异常也会记录。
        """
        if self.client:
            try:
                self.client.close()
                self.client = None
                logger.info(f"[port = {self.port}]Connection to Modbus device closed.")
            except Exception as e:
                logger.error(f"[port = {self.port}]Error during dis connect device: {e}")

    def do_gesture(self, gesture):
        """
        执行特定的手势动作。

        实际是向特定寄存器（ROH_FINGER_POS_TARGET0）写入手势数据。

        :param gesture: 要执行的手势数据。
        :return: 调用write_to_regesister方法的结果，即写入是否成功的布尔值。
        """
        return self.write_to_regesister(address=self.ROH_FINGER_POS_TARGET0, value=gesture[0]) and self.write_to_regesister(address=self.ROH_FINGER_POS_TARGET0, value=gesture[1]) 
    
    def count_motor_curtent(self):
        """
        计算电机电流的平均值。

        多次（最多MAX_NUM次）读取指定地址（ROH_FINGER_CURRENT0）的电流数据，然后计算这些数据的平均值并返回。

        :param address: 要读取电流数据的寄存器地址。
        :return: 一个包含6个电机电流平均值的列表。
        """
        sum_currents = [0] * 6
        ave_currents = [0] * 6
        max_error_times = 3  # 设定最多允许出现错误的次数
        error_count = 0
        for i in range(self.max_average_times):
            currents = self.read_from_register(address=self.ROH_FINGER_CURRENT0, count=6)
            if currents is None or currents.isError():
                error_count += 1
                logger.error("currents: read_holding_registers has an error \n")
                if error_count >= max_error_times:
                    raise ValueError("多次读取电流数据出现错误，无法计算平均值")
            else:
                currents_list = currents.registers if currents else []
                sum_currents = [sum_currents[j] + currents_list[j] for j in range(len(sum_currents))]
                time.sleep(0.2)
        ave_currents = [sum_currents[k] / self.max_average_times for k in range(len(sum_currents))]

        return ave_currents
        
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
    ports = ['COM4']
    node_ids = [2]
    main(ports = ports,node_ids = node_ids,aging_duration=1)