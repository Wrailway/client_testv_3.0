import time
import can

# 发送数据函数（与OHandSerialAPI接口匹配）
def send_data_impl(addr, data, length, context):
    """
    分帧发送数据，每帧最大8字节
    接口与OHandSerialAPI要求一致：(addr, data, length, context)
    """
    if not context:
        print("错误：null context")
        return 1

    can_interface = context
 
    if not can_interface or not hasattr(can_interface, "send"):
        print("错误：CAN总线未正确初始化")
        return 1

    try:
        for i in range(0, length, 8):
            current_size = min(8, length - i)
            # 创建CAN消息
            msg = can.Message(arbitration_id=addr, data=data[i : i + current_size], is_extended_id=False)
            # 发送消息
            can_interface.send(msg)
            # print(f"发送帧: ID=0x{addr:03X}, LEN={current_size}, DATA=", end="")
            # for byte in data[i : i + current_size]:
            #     print(f"{byte:02X} ", end="")
            # print()
        return 0
    except can.CanError as e:
        print(f"CAN发送失败，错误: {e}")
        return 1
    except Exception as e:
        print(f"发送异常: {e}")
        return 1


# 接收数据函数（与OHandSerialAPI接口匹配）
def recv_data_impl(context, api_instance=None):
    """
    接收CAN数据并处理
    接口与OHandSerialAPI要求一致：(context)
    """
    if not context:
        print("错误：null context")
        return 1

    can_interface = context
 
    if not can_interface or not hasattr(can_interface, "recv"):
        print("错误：CAN总线未正确初始化")
        return 1

    try:
        # 非阻塞接收（超时0.001秒）
        msg = can_interface.recv(timeout=0.005)
        if msg is not None:
            # 打印接收到的CAN帧信息
            # print(f"接收帧: ID=0x{msg.arbitration_id:03X}, LEN={msg.dlc}, DATA=", end="")
            # for byte in msg.data:
            #     print(f"{byte:02X} ", end="")
            # print()

            # 如果是发给主设备的消息，调用HAND_OnData处理
            if msg.arbitration_id == 0x01:  # ADDRESS_MASTER
                for byte in msg.data:
                    api_instance.HAND_OnData(byte)
    except can.CanError as e:
        print(f"CAN接收错误: {e}")
    except Exception as e:
        print(f"接收异常: {e}")


# 时间相关函数
_start_time = None


def get_milli_seconds_impl():
    """返回自程序启动以来的毫秒数"""
    global _start_time
    if _start_time is None:
        _start_time = time.time() * 1000  # 初始化开始时间
    return int(time.time() * 1000 - _start_time)


def delay_milli_seconds_impl(ms):
    """暂停执行指定的毫秒数"""
    time.sleep(ms / 1000.0)


# CAN初始化函数
def CAN_Init(port_name, baudrate):
    """初始化CAN总线连接，返回can.interface.Bus实例"""
    try:
        port_num = int(port_name)
        if port_num < 1 or port_num > 16:
            print(f"\n错误: 无效的端口号{port_name}，必须是1-16之间的数字")
            return None

        if baudrate not in [250000, 500000, 1000000]:
            print(f"\n错误: 不支持的波特率{baudrate}，必须是250000、500000或1000000")
            return None

        bus = can.interface.Bus(interface="pcan", channel=f"PCAN_USBBUS{port_num}", bitrate=baudrate)
        print(f"\nCAN总线初始化成功: 端口={port_name}, 波特率={baudrate}")
        return bus

    except ValueError as e:
        print(f"\n错误: 端口名解析失败，{str(e)}")
        return None
    except can.CanError as e:
        print(f"\n错误: CAN初始化失败，{str(e)}")
        return None
    except Exception as e:
        print(f"\n初始化异常: {str(e)}")
        return None
    
# 资源释放函数
def CAN_Shutdown(private_data):
    """关闭CAN总线连接"""
    if private_data and hasattr(private_data, 'shutdown'):
        private_data.shutdown()
        print(f"\nCAN总线已关闭")

