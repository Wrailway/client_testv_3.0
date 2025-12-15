import datetime
import json
import logging
import os
import sys
import time
import concurrent.futures
from typing import List, Tuple
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
log_file_name = f'./log/GestureStressTest_log_{current_date}_{timestamp}.txt'

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

class GestureStressTest:
    def __init__(self):
        self.node_id = 2
        self.port = 'COM4'
        self.FRAMER_TYPE = FramerType.RTU
        self.client = None
        self.BAUDRATE = 115200
        self.FINGER_POS_TARGET_MAX_LOSS = 32
        self.ROH_FINGER_POS_TARGET0 = 1135
        self.MAX_CYCLE_NUM = 1# 测试循环的最大次数，初始为1
        # 定义28个手势动作，每个动作分两步完成
        self.initial_gesture = [0, 0, 0, 0, 0, 728]
        self.fist_gesture = [[0, 62258, 62258, 62258, 62258, 728], [36044, 62258, 62258, 62258, 62258, 728]]
        self.mouse_gesture = [[32768, 0, 0, 0, 45875, 728], [32768, 7864, 0, 7864, 45875, 728]]
        self.key_gesture = [[0, 36044, 62258, 62258, 62258, 728], [42598, 36044, 62258, 62258, 62258, 728]]
        self.point_gesture = [[0, 0, 62258, 62258, 62258, 728], [52428, 0, 62258, 62258, 62258, 728]]
        self.column_gesture = [[52428, 0, 64880, 64880, 64880, 728], [52428, 36044, 64880, 64880, 64880, 728]]
        self.palm_gesture = [[26214, 16384, 16384, 16384, 19661, 728], [26214, 16384, 16384, 16384, 16384, 728]]
        self.salute_gesture = [[29491, 0, 0, 0, 0, 728], [29491, 0, 0, 0, 0, 728]]
        self.chopstick_gesture = [[16384, 19661, 62258, 62258, 62258, 728], [16384, 45875, 62258, 62258, 62258, 728]]
        # self.power_gesture = [[0, 62258, 62258, 62258, 62258, 62258], [49151, 62258, 62258, 62258, 62258, 62258]]
        self.power_gesture = [[0, 62258, 62258, 62258, 62258, 62258], [40000, 62258, 62258, 62258, 62258, 62258]]
        self.grasp_gesture = [[27525, 29491, 32768, 27525, 24903, 62258], [27525, 29491, 32768, 27525, 24903, 62258]]
        self.lift_gesture = [[0, 22937, 22937, 22937, 22937, 62258], [39321, 62258, 62258, 62258, 62258, 62258]]
        self.plate_gesture = [[0, 9830, 11141, 9830, 11141, 62258], [62258, 9830, 11141, 9830, 11141, 62258]]
        self.buckle_gesture = [[36044, 0, 55705, 55705, 55705, 728], [36044, 29491, 55705, 55705, 55705, 62258]]
        self.pinch_ic_gesture = [[29491, 0, 62258, 62258, 62258, 728], [29491, 32768, 62258, 62258, 62258, 62258]]
        self.pinch_io_gesture = [[29491, 0, 0, 0, 0, 62258], [29491, 32768, 0, 0, 0, 62258]]
        self.pinch_tc_gesture = [[0, 29491, 62258, 62258, 62258, 62258], [32768, 29491, 62258, 62258, 62258, 62258]]
        self.pinch_to_gesture = [[0, 29491, 0, 0, 0, 62258], [32768, 29491, 0, 0, 0, 62258]]
        self.pinch_itc_gesture = [[0, 0, 62258, 62258, 62258, 728], [29491, 29491, 62258, 62258, 62258, 62258]]
        self.tripod_ic_gesture = [[30801, 0, 0, 62258, 62258, 62258], [30801, 30146, 32768, 62258, 62258, 62258]]
        self.tripod_io_gesture = [[30801, 0, 0, 0, 0, 62258], [30801, 30146, 32768, 0, 0, 62258]]
        self.tripod_tc_gesture = [[0, 30146, 32768, 62258, 62258, 62258], [30801, 30146, 32768, 62258, 62258, 62258]]
        self.tripod_to_gesture = [[0, 30146, 32768, 0, 0, 62258], [30801, 30146, 32768, 0, 0, 62258]]
        self.tripod_itc_gesture = [[0, 0, 0, 62258, 62258, 62258], [30801, 30146, 32768, 62258, 62258, 62258]]
        self.gun_gesture = [[0, 0, 62258, 62258, 62258, 728], [0, 0, 62258, 62258, 62258, 728]]
        self.love_gesture = [[0, 0, 0, 62258, 62258, 728], [0, 0, 0, 62258, 62258, 728]]
        self.swear_gesture = [[0, 62258, 0, 0, 62258, 728], [0, 62258, 0, 0, 62258, 728]]
        self.victory_gesture = [[62258, 0, 0, 62258, 62258, 728], [62258, 0, 0, 62258, 62258, 728]]
        self.six_gesture = [[0, 62258, 62258, 62258, 0, 728], [0, 62258, 62258, 62258, 0, 728]]

        self.gestures = self.create_gesture_dict()
        self.interval = 1.5
        
    def set_port(self,port):
        self.port = port
        
    def set_node_id(self,node_id=2):
        self.node_id = node_id
        
    def create_gesture_dict(self):
        gesture_dict = {
            'fist': self.fist_gesture,
            'mouse': self.mouse_gesture,
            'key': self.key_gesture,
            'point': self.point_gesture,
            'column': self.column_gesture,
            'palm': self.palm_gesture,
            'salute': self.salute_gesture,
            'chopstick': self.chopstick_gesture,
            'power': self.power_gesture,
            'grasp': self.grasp_gesture,
            'lift': self.lift_gesture,
            'plate': self.plate_gesture,
            'buckle': self.buckle_gesture,
            'pinch_ic': self.pinch_ic_gesture,
            'pinch_io': self.pinch_io_gesture,
            'pinch_tc': self.pinch_tc_gesture,
            'pinch_to': self.pinch_to_gesture,
            'pinch_itc': self.pinch_itc_gesture,
            'tripod_ic': self.tripod_ic_gesture,
            'tripod_io': self.tripod_io_gesture,
            'tripod_tc': self.tripod_tc_gesture,
            'tripod_to': self.tripod_to_gesture,
            'tripod_itc': self.tripod_itc_gesture,
            'gun': self.gun_gesture,
            'love': self.love_gesture,
            'swear': self.swear_gesture,
            'victory': self.victory_gesture,
            'six': self.six_gesture
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
        time.sleep(self.interval)
        return self.write_to_regesister(address=self.ROH_FINGER_POS_TARGET0, value=gesture)

    def judge_if_hand_broken(self, gesture):
        """
        判断设备是否损坏。

        通过读取指定地址的寄存器数据，并与给定的手势数据对比，如果有任何一个寄存器值与手势值的差值超过FINGER_POS_TARGET_MAX_LOSS则认为设备损坏。

        :param address: 要读取数据的寄存器地址。
        :param gesture: 用于对比的手势数据。
        :return: 一个布尔值，表示设备是否损坏。
        """
        is_broken = False
        response = self.read_from_register(address=self.ROH_FINGER_POS_TARGET0, count=6)
        if response is not None and not response.isError():
            for i in range(len(response.registers)):
                if abs(response.registers[i] - gesture[i]) > self.FINGER_POS_TARGET_MAX_LOSS:
                    is_broken = True
        return is_broken
    
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
    
test_title = '循环做28个手势，进行压测\n标准：各个手头无异常，手指不脱线'
expected = []
description = '循环做28个手势'
# 定义一个常量用于表示老化测试的时长单位转换（从小时转换为秒）
SECONDS_PER_HOUR = 3600

def main(ports: list = [], node_ids: list = [], aging_duration: float = 1.5) -> Tuple[str, List, str, bool]:
    """
    测试的主函数。

    创建 GestureStressTest 类的实例，设置端口号并连接设备，然后进行多次（最多 MAX_CYCLE_NUM 次）测试循环，
    在每次循环中获取电机电流并检查电流是否正常，根据结果设置 result 变量，最后断开设备连接并返回测试结果。

    :param ports: 要连接的设备端口号列表，默认为空列表。
    :param node_ids: 与端口号对应的设备节点ID列表，默认为空列表。
    :param aging_duration: 测试持续时长，默认为1，单位根据具体业务逻辑确定（可能是小时等）。
    :return: 包含测试标题、整体测试结果、最终测试结果、是否显示电流的元组。
    """
    final_result = '通过'
    overall_result = []
    connected_status = False
    need_show_current = False

    start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f'---------------------------------------------开始老化测试<开始时间：{start_time}>----------------------------------------------\n')
    logger.info('测试目的：循环做28个手势，进行压测')
    logger.info('标准：各个手头无异常，手指不脱线\n')
    try:
        start_time = time.time()
        end_time = start_time + aging_duration * 3600
        # end_time1 = start_time1 + 60
        round_num = 0
        while time.time() < end_time:
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
            with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
                futures = [executor.submit(test_single_port, port, node_id, connected_status) for port, node_id in zip(ports, node_ids)]
                for future in concurrent.futures.as_completed(futures):
                    port_result, _ = future.result()
                    overall_result.append(port_result)
                    for gesture_result in port_result["gestures"]:
                        if gesture_result["result"]!= "通过":
                            result = '不通过'
                            final_result = '不通过'
                            break
            logger.info(f"#################第 {round_num} 轮测试结束，测试结果：{result}#############\n")
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
    #     # 可以添加资源清理相关操作，比如关闭文件句柄等（如果有相关操作）
    #     logger.info("执行测试结束后的清理操作")
    end_time = datetime.datetime.now().strftime('%Y-m-%d %H:%M:%S')
    logger.info(f'---------------------------------------------老化测试结束，测试结果：{final_result}<结束时间：{end_time}>----------------------------------------------\n')
    return test_title, overall_result, need_show_current


def build_gesture_result(timestamp, gesture_name, result):
    """
    根据给定的时间戳、手势名称以及测试结果构建手势结果字典。
    """
    return {
        "timestamp": timestamp,
        "description": gesture_name,
        "expected": '',
        "content": '',
        "result": result,
        "comment": '无'
    }


def test_single_port(port, node_id, connected_status):
    gesture_stress_test = GestureStressTest()
    gesture_stress_test.set_port(port=port)
    gesture_stress_test.set_node_id(node_id=node_id)

    connected_status = gesture_stress_test.connect_device()
    port_result = {
        "port": port,
        "gestures": []
    }
    if connected_status:
        try:
            for gesture_name, gesture in gesture_stress_test.gestures.items():
                logger.info(f"[port = {port}]执行    ---->  {gesture_name}")
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
                # 做新的手势
                for ges in gesture:
                    gesture_stress_test.do_gesture(gesture=ges) 
                    
                # 复默认手势
                default_gesture_result = gesture_stress_test.do_gesture(gesture=gesture_stress_test.initial_gesture) and \
                                        not gesture_stress_test.judge_if_hand_broken(gesture=gesture_stress_test.initial_gesture)
                gesture_result = build_gesture_result(timestamp, gesture_name, "通过" if default_gesture_result else "不通过")
                port_result["gestures"].append(gesture_result)
        except Exception as e:
            logger.error(f"操作手势过程中发生错误：{e}\n")
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            gesture_result = build_gesture_result(timestamp, gesture_name, "不通过")
            gesture_result["comment"] = f'操作手势过程中发生错误：{e}'
            port_result["gestures"].append(gesture_result)
        finally:
            gesture_stress_test.disConnect_device()
    return port_result, connected_status

if __name__ == "__main__":
    ports = ['COM4']
    node_ids = [2]
    aging_duration = 0.001
    main(ports = ports, node_ids = node_ids, aging_duration = aging_duration)