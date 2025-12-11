import pytest
from asyncio import sleep
import logging

from OHandSerialAPI import HAND_RESP_SUCCESS, HAND_PROTOCOL_UART, MAX_MOTOR_CNT, MAX_THUMB_ROOT_POS, MAX_FORCE_ENTRIES, OHandSerialAPI
from can_interface import *

# 设置日志级别为INFO，获取日志记录器实例
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()

# 设置处理程序的日志级别为 INFO
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

ADDRESS_MASTER = 0x01
FINGER_ANGLE_TARGET_MIN_LOSS = 20
FINGER_ANGLE_TARGET_MAX_LOSS = 100
PID_MAX_LOSS = 1e-2
POS_MIN_LOSS = 200
POS_MAX_LOSS = 200
HAND_ID = 0X02
DELAY_MS = 2500 #单个写函数等待时间
DELAY_MS_FUN = 6000#每个case执行等待时间
DELAY_MS_DEVICE_REBOOT = 15000#设备重启等待时间
SKIP_CASE = True # 默认跳过添加mark的case

# 初始化 API 实例（pytest夹具）
@pytest.fixture
def serial_api_instance():
    can_interface_instance = None
    serial_api_instance = None

    try:
        can_interface_instance = CAN_Init(port_name="1", baudrate=1000000)
        if can_interface_instance is None:
            logger.info("port init failed\n")
            return 0
        protocol = HAND_PROTOCOL_UART
        serial_api_instance = OHandSerialAPI(can_interface_instance, protocol, ADDRESS_MASTER,
                                                   send_data_impl,
                                                   recv_data_impl)

        serial_api_instance.HAND_SetTimerFunction(get_milli_seconds_impl, delay_milli_seconds_impl)
        serial_api_instance.HAND_SetCommandTimeOut(255)
        logger.info(serial_api_instance.get_private_data())

        yield serial_api_instance
    except Exception as e:
        logger.info(f"\n初始化异常: {str(e)}")

    finally:
        if serial_api_instance and hasattr(serial_api_instance, "shutdown"):  # 检查是否有自定义关闭方法
            try:
                serial_api_instance.shutdown()
                # logger.info("API shutdown successfully")
            except Exception as e:
                logger.error(f"Error during API shutdown: {e}")

        if can_interface_instance and hasattr(can_interface_instance, "shutdown"):
            try:
                can_interface_instance.shutdown()
                # logger.info("CAN bus connection closed")
            except Exception as e:
                logger.error(f"Error closing CAN bus: {e}")

# --------------------------- GET 命令测试 ---------------------------

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetProtocolVersion(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    major, minor = [0], [0]
    err, major_get, minor_get  = serial_api_instance.HAND_GetProtocolVersion(HAND_ID, major, minor, [])
    assert err == HAND_RESP_SUCCESS, f"获取协议版本失败: err={err}"
    logger.info(f"成功获取协议版本: V{major_get}.{minor_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFirmwareVersion(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    major, minor, revision = [0], [0], [0]
    err, major_get, minor_get, revision_get = serial_api_instance.HAND_GetFirmwareVersion(HAND_ID, major, minor, revision, [])
    assert err == HAND_RESP_SUCCESS, f"获取固件版本失败: err={err}"
    logger.info(f"成功获固件版本: V{major_get}.{minor_get}.{revision_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetHardwareVersion(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    hw_type, hw_ver, boot_version = [0], [0],[0]
    err, hw_type_get, hw_ver_get, boot_version_get = serial_api_instance.HAND_GetHardwareVersion(HAND_ID, hw_type, hw_ver, boot_version, [])
    assert err == HAND_RESP_SUCCESS, f"获取硬件版本失败: err={err}"
    logger.info(f"成功获取硬件版本: V{hw_type_get}.{hw_ver_get}.{boot_version_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFingerPID(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    p = [0]
    i = [0]
    d = [0]
    g = [0]
    for finger_id in range(MAX_MOTOR_CNT):
        err, p_get, i_get,d_get,g_get= serial_api_instance.HAND_GetFingerPID(HAND_ID, finger_id, p, i, d, g, [])
        assert err == HAND_RESP_SUCCESS, f"获取手指p, i, d, g值失败: err={err}"
        logger.info(f"成功获取手指{finger_id} p, i, d, g值: {p_get},{i_get},{d_get},{g_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFingerCurrentLimit(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    current_limit = [0]
    for finger_id in range(MAX_MOTOR_CNT):
        err, current_limit_get = serial_api_instance.HAND_GetFingerCurrentLimit(HAND_ID, finger_id, current_limit, [])
        assert err == HAND_RESP_SUCCESS, f"获取手指电流限制值失败: err={err}"
        logger.info(f"成功获取手指{finger_id} 电流限制值: {current_limit_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFingerCurrent(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    current = [0]
    for finger_id in range(MAX_MOTOR_CNT):
        err, current_get = serial_api_instance.HAND_GetFingerCurrent(HAND_ID, finger_id, current, [])
        assert err == HAND_RESP_SUCCESS,f"获取手指电流值失败: err={err}"
        logger.info(f"成功获取手指{finger_id} 电流值: {current_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFingerForceTarget(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    force_target = [0]
    for finger_id in range(MAX_MOTOR_CNT-1):
        err, force_target_get = serial_api_instance.HAND_GetFingerForceTarget(HAND_ID, finger_id, force_target, [])
        assert err == HAND_RESP_SUCCESS,f"获取手指力量目标值失败: err={err}"
        logger.info(f"成功获取手指{finger_id} 力量目标值: {force_target_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFingerForce(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    force_entry_cnt = [0]
    force = [0] * MAX_FORCE_ENTRIES
    for finger_id in range(MAX_MOTOR_CNT):
        err, force_get = serial_api_instance.HAND_GetFingerForce(HAND_ID, finger_id, force_entry_cnt, force, [])
        assert err == HAND_RESP_SUCCESS,f"获取手指当前力量值失败: err={err}"
        logger.info(f"成功获取手指{finger_id} 力量目标值: {force_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFingerPosLimit(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    low_limit = [0]
    high_limit = [0]
    for finger_id in range(MAX_MOTOR_CNT):
        err, low_limit_get,high_limit_get = serial_api_instance.HAND_GetFingerPosLimit(HAND_ID, finger_id, low_limit, high_limit, [])
        assert err == HAND_RESP_SUCCESS,f"获取手指绝对位置限制值失败: err={err}"
        logger.info(f"成功获取手指{finger_id} 绝对位置限制值: {low_limit_get}, {high_limit_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFingerPosAbs(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    target_pos = [0]
    current_pos = [0]
    for finger_id in range(MAX_MOTOR_CNT):
        err, target_pos_get, current_pos_get= serial_api_instance.HAND_GetFingerPosAbs(HAND_ID, finger_id, target_pos, current_pos, [])
        assert err == HAND_RESP_SUCCESS,f"获取手指绝当前绝对位置值失败: err={err}"
        logger.info(f"成功获取手指{finger_id} 当前绝对位置值: {target_pos_get}, {current_pos_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFingerPos(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    target_pos = [0]
    current_pos = [0]
    for finger_id in range(MAX_MOTOR_CNT):
        err, target_pos_get, current_pos_get = serial_api_instance.HAND_GetFingerPos(HAND_ID, finger_id, target_pos, current_pos, [])
        assert err == HAND_RESP_SUCCESS,f"获取手指绝当前逻辑位置值失败: err={err}"
        logger.info(f"成功获取手指{finger_id} 当前逻辑位置值: {target_pos_get}, {current_pos_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFingerAngle(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    target_angle = [0]
    current_angle = [0]
    for  finger_id in range(MAX_MOTOR_CNT):
        err, target_angle_get, current_angle_get= serial_api_instance.HAND_GetFingerAngle(HAND_ID, finger_id, target_angle, current_angle, [])
        assert err == HAND_RESP_SUCCESS,f"获取手指第一关节角度值失败:err={err}"
        logger.info(f"成功获取手指{finger_id} 第一关节角度值: {target_angle_get}, {current_angle_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetThumbRootPos(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    raw_encoder = [0]
    pos = [0]
    err, raw_encoder_get, pos_get = serial_api_instance.HAND_GetThumbRootPos(HAND_ID, raw_encoder, pos, [])
    assert err == HAND_RESP_SUCCESS,f"获取大拇指旋转预设位置值失败: err={err}"
    logger.info(f"成功获取大拇指旋转预设位置值: {raw_encoder_get}, {pos_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFingerPosAbsAll(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    target_pos = [0] * MAX_MOTOR_CNT
    current_pos = [0] * MAX_MOTOR_CNT
    motor_cnt = [MAX_MOTOR_CNT]
    err, target_pos_get,current_pos_get= serial_api_instance.HAND_GetFingerPosAbsAll(HAND_ID, target_pos, current_pos, motor_cnt, [])
    assert err == HAND_RESP_SUCCESS,f"获取所有手指当前的绝对位置值失败: err={err}"
    logger.info(f"成功获取所有手指当前的绝对位置值: {target_pos_get}, {current_pos_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFingerPosAll(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    target_pos = [0] * MAX_MOTOR_CNT
    current_pos = [0] * MAX_MOTOR_CNT
    motor_cnt = [MAX_MOTOR_CNT]
    remote_err = []
    err, target_pos_get,current_pos_get = serial_api_instance.HAND_GetFingerPosAll(HAND_ID, target_pos, current_pos, motor_cnt, remote_err)
    assert err == HAND_RESP_SUCCESS,f"获取所有手指当前的逻辑位置值失败: err={err}"
    logger.info(f"成功获取所有手指当前的逻辑位置值:  {target_pos_get}, {current_pos_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetFingerAngleAll(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    target_angle = [0] * MAX_MOTOR_CNT
    current_angle = [0] * MAX_MOTOR_CNT
    motor_cnt = [MAX_MOTOR_CNT]
    err, remtarget_angle_get, current_angle_get= serial_api_instance.HAND_GetFingerAngleAll(HAND_ID, target_angle, current_angle, motor_cnt, [])
    assert err == HAND_RESP_SUCCESS,f"获取所有手指值失败: err={err}"
    logger.info(f"成功获取所有手指当前的逻辑位置值: {remtarget_angle_get}, {current_angle_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')    
def test_HAND_GetFingerForcePID(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    p = [0]
    i = [0]
    d = [0]
    g = [0]
    for finger_id in range(MAX_MOTOR_CNT-1): #拇指旋转没带
        err, p_get,i_get, d_get, g_get = serial_api_instance.HAND_GetFingerForcePID(HAND_ID, finger_id, p, i, d, g, [])
        assert err == HAND_RESP_SUCCESS,f"获取手指力量p, i, d, g值失败: err={err}"
        logger.info(f"成功获取手指{finger_id} 力量p, i, d, g值: {p_get}, {i_get},{d_get},{g_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetSelfTestLevel(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    self_test_level = [0]
    err, self_test_level_get = serial_api_instance.HAND_GetSelfTestLevel(HAND_ID, self_test_level, [])
    assert err == HAND_RESP_SUCCESS,f"获取手自检开关状态失败: err={err}"
    logger.info(f"成功获取手自检开关状态: {self_test_level_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetBeepSwitch(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    beep_switch = [0]
    err, beep_switch_get = serial_api_instance.HAND_GetBeepSwitch(HAND_ID, beep_switch, [])
    assert err == HAND_RESP_SUCCESS,f"获取手蜂鸣器开关状态失败: err={err}"
    logger.info(f"成功获取手蜂鸣器开关状态: {beep_switch_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetButtonPressedCnt(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    pressed_cnt = [0]
    err, pressed_cnt_get = serial_api_instance.HAND_GetButtonPressedCnt(HAND_ID, pressed_cnt, [])
    assert err == HAND_RESP_SUCCESS,f"获取手按钮按下次数值失败:  err={err}"
    logger.info(f"成功获取手按钮按下次数值: {pressed_cnt_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_GetUID(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    uid_w0 = [0]
    uid_w1 = [0]
    uid_w2 = [0]
    err, uid_w0_get,uid_w1_get,uid_w2_get = serial_api_instance.HAND_GetUID(HAND_ID, uid_w0, uid_w1, uid_w2, [])
    assert err == HAND_RESP_SUCCESS,f"获取手UID值失败: err={err}"
    logger.info(f"成功获取手UID值: {uid_w0_get},{uid_w1_get},{uid_w2_get}")
    
@pytest.mark.skipif(True,reason='功能未实现，只返回err，先跳过')
def test_HAND_GetBatteryVoltage(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    voltage = [0]
    err = serial_api_instance.HAND_GetBatteryVoltage(HAND_ID, voltage, [])
    assert err == HAND_RESP_SUCCESS,f"获取手电池电压值失败: err={err}"
    logger.info(f"成功获取手电池电压值: {voltage[0]}")
    
@pytest.mark.skipif(True,reason='功能未实现，只返回err，先跳过')
def test_HAND_GetUsageStat(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    total_use_time = [0]
    total_open_times = [0]
    motor_cnt = MAX_MOTOR_CNT
    err = serial_api_instance.HAND_GetUsageStat(HAND_ID, total_use_time, total_open_times, motor_cnt, [])
    assert err == HAND_RESP_SUCCESS,f"获取手使用数据值失败: err={err}"
    logger.info(f"成功获取手使用数据值: {total_use_time},{total_use_time}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')    
def test_GetCalidata(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    end_pos = [0] * MAX_MOTOR_CNT
    start_pos = [0] * MAX_MOTOR_CNT
    motor_cnt = [MAX_MOTOR_CNT]
    thumb_root_pos = [0] * MAX_THUMB_ROOT_POS
    thumb_root_pos_cnt = [3]  # 初始请求3个拇指根位置数据
    err, end_pos_get, start_pos_get, thumb_root_pos_get = serial_api_instance.HAND_GetCaliData(HAND_ID, end_pos, start_pos, motor_cnt, thumb_root_pos, thumb_root_pos_cnt, [])
    assert err == HAND_RESP_SUCCESS, f"获取矫正数据失败: {err}"
    logger.info(f"成功获取矫正数据, end_pos: {end_pos_get}, start_pos: {start_pos_get}, thumb_root_pos: {thumb_root_pos_get}, ")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')    
def test_GetfingerStopParams(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    speed, stop_current, stop_after_period, retry_interval = [0], [0], [0], [0]
    for i in range(MAX_MOTOR_CNT):
        err, speed_get, stop_current_get, stop_after_period_get, retry_interval_get = serial_api_instance.HAND_GetFingerStopParams(HAND_ID, i, speed, stop_current, stop_after_period, retry_interval, [])
        assert err == HAND_RESP_SUCCESS, f"获取手指停止参数失败: {err}"
        logger.info(f"成功获取手指停止参数: 速度: {speed_get}, 暂停电流:{stop_current_get}, 暂停间隔:{stop_after_period_get}, 重试间隔:{retry_interval_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')        
def test_GetManufactureData(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    sub_model, hw_revision, serial_number, customer_tag = [0], [0], [0], [0]
    err, sub_model_get, hw_revision_get, serial_number_get, customer_tag_get = serial_api_instance.HAND_GetManufactureData(HAND_ID, sub_model, hw_revision, serial_number, customer_tag, [])
    assert err == HAND_RESP_SUCCESS, f"manufacture_data_get: {err}\n"
    logger.info(f"sub_model: {sub_model_get}, hw_revision: {hw_revision_get}, serial_number: {serial_number_get}, customer_tag: {customer_tag_get}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_GetFingerSpeedCtrlParams(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    brake_distance, accel_distance, speed_ratio = [0], [0], [0]
    err, brake_distance_get, accel_distance_get, speed_ratio_get = serial_api_instance.HAND_GetFingerSpeedCtrlParams(HAND_ID, brake_distance, accel_distance, speed_ratio, [])
    assert err == HAND_RESP_SUCCESS, f"test_speed_ctrl_params_get: {err}\n"
    logger.info(f"brake_distance: {brake_distance_get}, accel_distance: {accel_distance_get}, speed_ratio: {speed_ratio_get}")


# # --------------------------- SET 命令测试 ---------------------------
@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_Reset(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    RESET_MODE ={
        '工作模式':0,
        'DFU模式':1
    }
    # mode = 0
    remote_err = []

    err = serial_api_instance.HAND_Reset(HAND_ID, RESET_MODE.get('工作模式'), remote_err)
    assert err == HAND_RESP_SUCCESS,f"设置手重置失败: err={err}"
    logger.info(f'设置手重置重启到工作模式成功')
    delay_milli_seconds_impl(DELAY_MS_DEVICE_REBOOT)
    
    err = serial_api_instance.HAND_Reset(HAND_ID, RESET_MODE.get('DFU模式'), remote_err)
    assert err == HAND_RESP_SUCCESS,f"设置手重置失败: err={err}"
    logger.info(f'设置手重置重启到DFU模式成功')
    delay_milli_seconds_impl(DELAY_MS_DEVICE_REBOOT)
    
    logger.info('恢复默认值')
    err = serial_api_instance.HAND_Reset(HAND_ID, RESET_MODE.get('工作模式'), remote_err)
    assert err == HAND_RESP_SUCCESS,f"恢复默认值失败: err={err}"
    logger.info('恢复默认值成功')
    delay_milli_seconds_impl(DELAY_MS_DEVICE_REBOOT)
    
@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_PowerOff(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    remote_err = []
    err = serial_api_instance.HAND_PowerOff(HAND_ID, remote_err)
    assert err == HAND_RESP_SUCCESS,f"设置关机失败: err={err},remote_err={remote_err[0]}"
    logger.info('设置关机成功成功')
    delay_milli_seconds_impl(DELAY_MS_DEVICE_REBOOT)

@pytest.mark.skipif(SKIP_CASE,reason='debug中，先跳过')
def test_HAND_SetID(serial_api_instance):
    """测试设置设备ID功能（单函数实现，适配pytest夹具）"""
    delay_milli_seconds_impl(DELAY_MS_FUN)
    test_results = []
    original_id = HAND_ID  # 初始ID（与夹具保持一致）
    try:
        # 定义测试用例（ID有效范围：3-247）
        test_cases = [
            (3,     "有效ID-最小值3"),  # 修正数值与描述匹配
            (125,   "有效ID-中间值125"),
            (247,   "有效ID-最大值247"),
            (1,     "无效ID-边界值1"),
            (0,     "无效ID-边界值0"),
            (-1,    "无效ID-负数-1"),
            (248,   "无效ID-边界值248"),
            (256,   "无效ID-超出字节范围256")
        ]

        for new_id, desc in test_cases:
            logger.info(f"\n===== 测试ID设置：{desc} =====")
            remote_err = []
            current_api = serial_api_instance  # 默认使用夹具的原始实例

            # 1. 发送设置ID命令
            set_err = current_api.HAND_SetID(original_id, new_id, remote_err)
            logger.info(f"设置ID {new_id} 结果：错误码={set_err}, 远程错误={remote_err}")

            # 2. 验证有效ID（2-247）
            if 2 <= new_id <= 247:
                # 断言设置命令成功
                assert set_err == HAND_RESP_SUCCESS, \
                    f"有效ID {new_id} 设置失败，错误码={set_err}, 远程错误={remote_err}"
                
                # 等待设备重启应用新ID（根据实际设备调整等待时间）
                delay_milli_seconds_impl(DELAY_MS*2)

                # 验证新ID通信有效性（通过查询协议版本间接验证）
                major, minor = [0], [0]
                # 修复返回值解包：若函数返回单个int则无需解包
                verify_err,_,_ = serial_api_instance.HAND_GetProtocolVersion(new_id, major, minor, [])
                assert verify_err == HAND_RESP_SUCCESS, \
                    f"新ID {new_id} 通信失败，验证错误码={verify_err}"
                
                logger.info(f"新ID {new_id} 验证通过，开始恢复原始ID...")
                # 恢复原始ID（使用新ID的实例发送恢复命令）
                recover_err = serial_api_instance.HAND_SetID(new_id, original_id, [])
                assert recover_err == HAND_RESP_SUCCESS, \
                    f"恢复原始ID {original_id} 失败，错误码={recover_err}"
                
                # 等待恢复生效
                delay_milli_seconds_impl(DELAY_MS*2)

                # 验证原始ID恢复成功
                recover_verify_err,_,_ = serial_api_instance.HAND_GetProtocolVersion(original_id, major, minor, [])
                assert recover_verify_err == HAND_RESP_SUCCESS, \
                    f"原始ID {original_id} 恢复后通信失败，错误码={recover_verify_err}"
                
                test_results.append((desc, "通过"))

            # 3. 验证无效ID（非2-247）
            else:
                # 断言设置命令失败
                assert set_err != HAND_RESP_SUCCESS, \
                    f"无效ID {new_id} 设置未被拒绝，错误码={set_err}, 远程错误={remote_err}"
                test_results.append((desc, "通过（预期失败）"))

    except AssertionError as e:
        logger.info(f"测试断言失败：{str(e)}")
        test_results.append((f"断言失败-{desc}", f"失败：{str(e)}"))
        raise  # 重新抛出异常，让pytest标记测试失败
    except Exception as e:
        logger.info(f"测试未预期异常：{str(e)}")
        test_results.append(("全局异常", f"失败：{str(e)}"))
        raise
    finally:
        # ========== 测试结果汇总 ==========
        logger.info("\n===== 设备ID设置测试结果汇总 =====")
        passed = sum(1 for _, res in test_results if "通过" in res)
        total = len(test_results)
        logger.info(f"总用例数：{total} | 通过：{passed} | 失败：{total - passed}")
        for case, result in test_results:
            logger.info(f"  {case}：{result}")
        logger.info("==================================")
        
def get_HAND_PID(serial_api_instance,finger_id):
    delay_milli_seconds_impl(DELAY_MS)
    p = [0]
    i = [0]
    d = [0]
    g = [0]
    return serial_api_instance.HAND_GetFingerPID(HAND_ID, finger_id, p, i, d, g, [])

def get_HAND_FORCE_PID(serial_api_instance,finger_id):
    delay_milli_seconds_impl(DELAY_MS)
    p = [0]
    i = [0]
    d = [0]
    g = [0]
    return serial_api_instance.HAND_GetFingerForcePID(HAND_ID, finger_id, p, i, d, g, [])
            
@pytest.mark.skipif(SKIP_CASE,reason='连续设置多个手指参数报错，提bug：#5722，#5723 ，先跳过')
def test_HAND_SetFingerPID(serial_api_instance):
    """手指PID参数设置功能测试 - 单变量控制"""
    delay_milli_seconds_impl(DELAY_MS_FUN)
    # 默认参数值
    DEFAULT_P = 250.00
    DEFAULT_I = 2.00
    DEFAULT_D = 250.00
    DEFAULT_G = 1.00
    # 定义各参数的测试值(包含有效/边界/无效值)
    PARAM_TEST_DATA = {
        'P': [
            (1.00,   "P值最小值1.00"),
            (240.00, "P值中间值240.00"),
            (500.00, "P值最大值500.00"),
            (0.90,    "P值边界值0.9"),
            (0.00,     "P值边界值0.00"),
            (-1.00,    "P值边界值-1.00"),
            (501.00, "P值边界值501.00"),
            (65535.00, "P值边界值65535.00"),
            (65536.00, "P值边界值65536.00")
        ],
        'I': [
            (0.00,     "I值最小值0.00"),
            (50.00,  "I值中间值50.00"),
            (100.00, "I值最大值100.00"),
            (-1.00,    "I值边界值-1.00"),
            (101.00, "I值边界值101.00"),
            (65535.00, "I值边界值65535.00"),
            (65536.00, "I值边界值65536.00")
        ],
        'D': [
            (0.00,     "D值最小值0.00"),
            (240.00, "D值中间值240.00"),
            (500.00, "D值最大值500.00"),
            (-1.00,    "D值边界值-1.00"),
            (501.00, "D值边界值501.00"),
            (65535.00, "D值边界值65535.00"),
            (65536.00, "D值边界值65536.00")
        ],
        'G': [
            (0.01,     "G值最小值0.01"),
            (0.50,    "G值中间值0.50"),
            (1.00,   "G值最大值1.00"),
            (0.00,     "G值边界值0.00"),
            (-1.00,    "G值边界值-1.00"),
            (1.05,   "G值边界值1.05"),
            (65535.00, "G值边界值65535.00"),
            (65536.00, "G值边界值65536.00")
        ]
    }
    
    # 测试结果存储
    test_results = []
    
    try:
        """------------------- 单变量测试 -------------------"""
    # 定义测试常量
        for finger_id in range(MAX_MOTOR_CNT):
            logger.info(f"\n===== 开始测试手指 {finger_id} =====")
            # 测试P参数
            logger.info(f"测试手指 {finger_id} 的P参数")
            for p_value, desc in PARAM_TEST_DATA['P']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerPID(
                    HAND_ID, finger_id, 
                    p_value,        # 测试变量P
                    DEFAULT_I,      # I固定为默认值
                    DEFAULT_D,      # D固定为默认值
                    DEFAULT_G,      # G固定为默认值
                    remote_err
                )
                
                # 验证结果
                if 1.00 <= p_value <= 500.00:  # 有效P值范围
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效P值失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                        
                    delay_milli_seconds_impl(DELAY_MS)
                    value = get_HAND_PID(serial_api_instance,finger_id)
                    assert value[0] == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 获取有效P值失败: {desc}, 错误码: err={err}"
                    assert abs(p_value - value[1]) < PID_MAX_LOSS, \
                        f"手指 {finger_id} 设置的P值: {p_value}, 与读取的P值:{value[1]}不一致"
                    test_results.append((f"手指{finger_id} P值测试({desc})", "通过"))
                else:  # 无效P值
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效P值未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} P值测试({desc})", "通过(预期失败)"))
            
            # 测试I参数
            logger.info(f"测试手指 {finger_id} 的I参数")
            for i_value, desc in PARAM_TEST_DATA['I']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerPID(
                    HAND_ID, finger_id, 
                    DEFAULT_P,      # P固定为默认值
                    i_value,        # 测试变量I
                    DEFAULT_D,      # D固定为默认值
                    DEFAULT_G,      # G固定为默认值
                    remote_err
                )
                # 验证结果
                if 0.00 <= i_value <= 100.00:  # 有效I值范围
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效I值失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    delay_milli_seconds_impl(DELAY_MS)
                    value = get_HAND_PID(serial_api_instance,finger_id)
                    assert value[0] == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 获取有效I值失败: {desc}, 错误码: err={err}"
                    assert abs(i_value - value[2]) < PID_MAX_LOSS, \
                        f"手指 {finger_id} 设置的I值: {i_value}, 与读取的I值:{value[2]}不一致"
                    test_results.append((f"手指{finger_id} I值测试({desc})", "通过"))
                else:
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效I值未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} I值测试({desc})", "通过(预期失败)"))
            
            # 测试D参数(代码结构与I参数测试类似)
            logger.info(f"测试手指 {finger_id} 的D参数")
            for d_value, desc in PARAM_TEST_DATA['D']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err  = serial_api_instance.HAND_SetFingerPID(
                    HAND_ID, finger_id, 
                    DEFAULT_P,      # P固定为默认值
                    DEFAULT_I,      # I固定为默认值
                    d_value,        # 测试变量d
                    DEFAULT_G,      # G固定为默认值
                    remote_err
                )
                # 验证结果
                if 0.0 <= d_value <= 500.00:  # 有效D值范围
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效D值失败: {desc}, 错误码:  err={err},remote_err={remote_err[0]}"
                    delay_milli_seconds_impl(DELAY_MS)
                    value = get_HAND_PID(serial_api_instance,finger_id)
                    assert value[0] == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 获取有效D值失败: {desc}, 错误码: err={err}"
                    assert abs(d_value - value[3]) < PID_MAX_LOSS, \
                        f"手指 {finger_id} 设置的D值: {d_value}, 与读取的D值:{value[3]}不一致"
                    test_results.append((f"手指{finger_id} D值测试({desc})", "通过"))
                else:
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效D值未报错: {desc}, 错误码:  err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} D值测试({desc})", "通过(预期失败)"))
                    
            # 测试G参数(代码结构与I参数测试类似)
            logger.info(f"测试手指 {finger_id} 的G参数")
            for g_value, desc in PARAM_TEST_DATA['G']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerPID(
                    HAND_ID, finger_id, 
                    DEFAULT_P,      # P固定为默认值
                    DEFAULT_I,      # I固定为默认值
                    DEFAULT_D,      # D固定为默认值
                    g_value,        # 测试变量g
                    remote_err
                )
                # 验证结果
                if 0.01 <= g_value <= 1.00:  # 有效G值范围
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效G值失败: {desc}, 错误码:err={err},remote_err={remote_err[0]}"
                    delay_milli_seconds_impl(DELAY_MS)
                    value = get_HAND_PID(serial_api_instance,finger_id)
                    assert value[0] == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 获取有效G值失败: {desc}, 错误码: err={err}"
                    assert abs(g_value - value[4]) < PID_MAX_LOSS, \
                        f"手指 {finger_id} 设置的G值: {g_value}, 与读取的G值:{value[4]}不一致"
                    test_results.append((f"手指{finger_id} G值测试({desc})", "通过"))
                else:
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效G值未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} G值测试({desc})", "通过(预期失败)"))
            
            logger.info(f"手指 {finger_id} 所有参数测试完成")
        
        """------------------- 恢复默认值 -------------------"""
        logger.info("\n===== 恢复所有手指的默认PIDG值 =====")
        for finger_id in range(MAX_MOTOR_CNT):
            remote_err = []
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetFingerPID(
                HAND_ID, finger_id, 
                DEFAULT_P, DEFAULT_I, DEFAULT_D, DEFAULT_G, remote_err
            )
            assert err == HAND_RESP_SUCCESS, \
                f"恢复手指 {finger_id} 默认值失败, 错误码: err={err},remote_err={remote_err[0]}"
            logger.info(f"手指 {finger_id} 已恢复默认值")
    
    except AssertionError as e:
        logger.error(f"测试失败: {str(e)}")
        raise  # 重新抛出原始错误
    
    finally:
        """------------------- 测试结果汇总 -------------------"""
        logger.info("\n===== 测试结果汇总 =====")
        passed = sum(1 for case, result in test_results if "通过" in result)
        total = len(test_results)
        logger.info(f"总测试用例: {total}, 通过: {passed}, 失败: {total - passed}")
        
        for case, result in test_results:
            logger.info(f"{case}: {result}")
        logger.info("=======================")

@pytest.mark.skipif(SKIP_CASE,reason='debug中，先跳过')
def test_HAND_SetFingerCurrentLimit(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    # 默认参数值
    DEFAULT_CURRENT = 1299
    # 定义各参数的测试值(包含有效/边界/无效值)
    PARAM_TEST_DATA = {
        'current_limit': [
            (0,     "电流最小值0"),
            (600,   "电流值600"),
            (1299,  "电流值1299"),
            (1300,  "电流值1300"),
            (65535, "电流边最大65535"),
            (65536, "电流边界65536"),
            (-1,    "电流边界值-1")
        ]
    }
    
    # 测试结果存储
    test_results = []
    
    try:
        """------------------- 单变量测试 -------------------"""
        for finger_id in range(MAX_MOTOR_CNT):
            logger.info(f"\n===== 开始测试手指 {finger_id} 的电流限制 =====")
            
            # 测试电流限制参数
            for current_limit, desc in PARAM_TEST_DATA['current_limit']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerCurrentLimit(
                    HAND_ID, finger_id, 
                    current_limit,  # 测试变量电流限制值
                    remote_err
                )
                
                # 验证结果（假设有效范围：0-1299）
                if 0 <= current_limit <= 65535:  # 有效电流范围
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效电流值失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} 电流测试({desc})", "通过"))
                else:  # 无效电流值
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效电流值未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} 电流测试({desc})", "通过(预期失败)"))
            
            logger.info(f"手指 {finger_id} 电流限制测试完成")
        
        """------------------- 恢复默认值 -------------------"""
        logger.info("\n===== 恢复所有手指的默认电流限制 =====")
        for finger_id in range(MAX_MOTOR_CNT):
            remote_err = []
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetFingerCurrentLimit(
                HAND_ID, finger_id, 
                DEFAULT_CURRENT, remote_err
            )
            assert err == HAND_RESP_SUCCESS, \
                f"恢复手指 {finger_id} 默认电流失败, 错误码:err={err},remote_err={remote_err[0]}"
            logger.info(f"手指 {finger_id} 已恢复默认电流值: {DEFAULT_CURRENT}")
    
    except AssertionError as e:
        logger.error(f"测试失败: {str(e)}")
        raise  # 重新抛出原始错误
    
    finally:
        """------------------- 测试结果汇总 -------------------"""
        logger.info("\n===== 电流限制测试结果汇总 =====")
        passed = sum(1 for case, result in test_results if "通过" in result)
        total = len(test_results)
        logger.info(f"总测试用例: {total}, 通过: {passed}, 失败: {total - passed}")
        
        for case, result in test_results:
            logger.info(f"{case}: {result}")
        logger.info("=======================")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_SetFingerForceTarget(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    # 默认参数值
    DEFAULT_FORCE_TARGET = 0
    # 定义各参数的测试值(包含有效/边界/无效值)
    PARAM_TEST_DATA = {
        'force_target': [
            (0,          "目标力最小值0"),
            (1,          "目标力值1"),
            (32767,      "目标力中间值32767"),
            (65535,      "目标力最大值65535"),
            (-1,         "目标力边界值-1"),
            (65536,      "目标力边界值65536")
        ]
    }
    
    # 测试结果存储
    test_results = []
    
    try:
        """------------------- 单变量测试 -------------------"""
        for finger_id in range(MAX_MOTOR_CNT-1):
            logger.info(f"\n===== 开始测试手指 {finger_id} 的目标力设置 =====")
            
            # 测试目标力参数
            for force_target, desc in PARAM_TEST_DATA['force_target']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerForceTarget(
                    HAND_ID, finger_id, 
                    force_target,  # 测试变量目标力值
                    remote_err
                )
                
                # 验证结果（假设有效范围：0-65535）
                if 0 <= force_target <= 65535:  # 有效目标力范围（16位无符号整数）
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效目标力失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} 目标力测试({desc})", "通过"))
                else:  # 无效目标力值
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效目标力未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} 目标力测试({desc})", "通过(预期失败)"))
                    
                """------------------- 单个手指测试完成后立即恢复默认值 -------------------"""
                logger.info(f"\n===== 恢复手指 {finger_id} 的默认目标力 =====")
                remote_err_reset = []
                delay_milli_seconds_impl(DELAY_MS)
                err_reset = serial_api_instance.HAND_SetFingerForceTarget(
                    HAND_ID, finger_id, 
                    DEFAULT_FORCE_TARGET, 
                    remote_err_reset
                )
                assert err_reset == HAND_RESP_SUCCESS, \
                    f"恢复手指 {finger_id} 默认目标力失败, 错误码: err={err_reset},remote_err={remote_err_reset[0] if remote_err_reset else '无'}"
                logger.info(f"手指 {finger_id} 已恢复默认目标力: {DEFAULT_FORCE_TARGET}")
            
            logger.info(f"手指 {finger_id} 目标力设置测试完成")
        
        """------------------- 恢复默认值 -------------------"""
        logger.info("\n===== 恢复所有手指的默认目标力 =====")
        for finger_id in range(MAX_MOTOR_CNT-1):
            remote_err = []
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetFingerForceTarget(
                HAND_ID, finger_id, 
                DEFAULT_FORCE_TARGET, remote_err
            )
            assert err == HAND_RESP_SUCCESS, \
                f"恢复手指 {finger_id} 默认目标力失败, 错误码: err={err},remote_err={remote_err[0]}"
            logger.info(f"手指 {finger_id} 已恢复默认目标力: {DEFAULT_FORCE_TARGET}")
    
    except AssertionError as e:
        logger.error(f"测试失败: {str(e)}")
        raise  # 重新抛出原始错误
    
    finally:
        """------------------- 测试结果汇总 -------------------"""
        logger.info("\n===== 目标力设置测试结果汇总 =====")
        passed = sum(1 for case, result in test_results if "通过" in result)
        total = len(test_results)
        logger.info(f"总测试用例: {total}, 通过: {passed}, 失败: {total - passed}")
        
        for case, result in test_results:
            logger.info(f"{case}: {result}")
        logger.info("=======================")

def get_FingerPosLimit(serial_api_instance,finger_id):
    delay_milli_seconds_impl(DELAY_MS*2)
    low_limit = [0]
    high_limit = [0]
    return serial_api_instance.HAND_GetFingerPosLimit(HAND_ID, finger_id, low_limit, high_limit, [])
        
@pytest.mark.skipif(SKIP_CASE,reason='超出范围值(校准范围)，不报无效值错误，提bug: #5738,先跳过')
def test_HAND_SetFingerPosLimit(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    # 定义测试常量
    end_pos = [0] * MAX_MOTOR_CNT
    start_pos = [0] * MAX_MOTOR_CNT
    motor_cnt = [MAX_MOTOR_CNT]
    thumb_root_pos = [0] * MAX_THUMB_ROOT_POS
    thumb_root_pos_cnt = [3]  # 初始请求3个拇指根位置数据
    # 获取每个手指的校准数据（列表类型，索引对应finger_id）
    err, end_pos_get, start_pos_get, thumb_root_pos_get = serial_api_instance.HAND_GetCaliData(
        HAND_ID, end_pos, start_pos, motor_cnt, thumb_root_pos, thumb_root_pos_cnt, []
    )
    assert err == HAND_RESP_SUCCESS, f"获取矫正数据失败: {err}"  # 确保数据获取成功

    # 测试结果存储
    test_results = []
    logger.info(f'start_pos_get={start_pos_get}')
    logger.info(f'end_pos_get={end_pos_get}')
    try:
        """------------------- 按手指逐个测试 -------------------"""
        for finger_id in range(MAX_MOTOR_CNT):
            logger.info(f"\n===== 开始测试手指 {finger_id} 的位置限制 =====")
            delay_milli_seconds_impl(DELAY_MS)
            # 获取当前手指的起始/结束位置（从列表中提取单个值）
            current_start = start_pos_get[finger_id]
            current_end = end_pos_get[finger_id]
    
            # 定义当前手指的测试数据（基于该手指的实际校准值）
            param_test_data = {
                'pos_limit': [
                    # 有效范围测试
                    (current_start, current_end, "正常范围"),
                    (current_start, current_start, "下限等于上限"),
                    (current_start, current_start + 1, "下限接近上限"),  # 单个值相加
                   
                    # # 无效范围测试
                    (0, 65535, "取全部范围"),
                    (current_end, current_start, "下限大于上限"),
                    (-1, 100, "下限为负数"),
                    (100, 65536, "上限超出范围"),
                    (-1, 65536, "上下限都无效")
                ]
            }
            
            # 测试当前手指的位置限制参数
            for min_pos, max_pos, desc in param_test_data['pos_limit']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerPosLimit(
                    HAND_ID, finger_id, 
                    min_pos,  # 下限
                    max_pos,  # 上限
                    remote_err
                )
                
                # 验证结果（基于当前手指的有效范围）
                if current_start <= min_pos <= max_pos <= current_end:
                    # 有效范围：上下限在0-65535之间，且下限<=上限
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效位置限制失败: {desc}, 错误码: err={err}, remote_err={remote_err[0]}"
                    delay_milli_seconds_impl(DELAY_MS)
                    value = get_FingerPosLimit(serial_api_instance,finger_id)
                    assert value[0] == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 获取有效位置限制失败, 错误码: err={err}"
                    # if min_pos < current_start:
                    #    assert abs(value[1]-current_start) < POS_MIN_LOSS, \
                    #    f"写入小于最小值{min_pos}(<{current_start})，但读取位置为{value[1]}（预期{current_start})"
                    # elif max_pos > current_end:
                    #     assert abs(value[2]-current_end) < POS_MIN_LOSS, \
                    #     f"写入大于最大值{max_pos}(>{current_end})，但读取位置为{value[2]}（预期{current_end})"
                    # else:
                    assert abs(value[1] - min_pos) < POS_MAX_LOSS and abs(value[2] - max_pos) < POS_MAX_LOSS, \
                            f"手指 {finger_id} 设置位置Limit{min_pos,max_pos}，读取位置{value[1],value[2]}，差值超出容差{POS_MAX_LOSS}"
                    test_results.append((f"手指{finger_id} 位置限制测试({desc})", "通过"))
                else:
                    # 无效范围：超出边界或下限>上限
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效位置限制未报错: {desc}, 错误码: err={err}, remote_err={remote_err}"
                    test_results.append((f"手指{finger_id} 位置限制测试({desc})", "通过(预期失败)"))
            logger.info(f"手指 {finger_id} 位置限制测试完成")
        
        """------------------- 恢复默认值 -------------------"""
        logger.info("\n===== 恢复所有手指的默认位置限制 =====")
        for finger_id in range(MAX_MOTOR_CNT):
            remote_err = []
            # 恢复当前手指的默认限制（使用该手指的校准值）
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetFingerPosLimit(
                HAND_ID, finger_id, 
                start_pos_get[finger_id],  # 单个手指的起始位置
                end_pos_get[finger_id],    # 单个手指的结束位置
                remote_err
            )
            assert err == HAND_RESP_SUCCESS, \
                f"恢复手指 {finger_id} 默认位置限制失败, 错误码: err={err}, remote_err={remote_err[0]}"
            logger.info(f"手指 {finger_id} 已恢复默认位置限制")
    
    except AssertionError as e:
        logger.error(f"测试失败: {str(e)}")
        raise  # 重新抛出原始错误
    
    finally:
        """------------------- 测试结果汇总 -------------------"""
        logger.info("\n===== 位置限制测试结果汇总 =====")
        passed = sum(1 for case, result in test_results if "通过" in result)
        total = len(test_results)
        logger.info(f"总测试用例: {total}, 通过: {passed}, 失败: {total - passed}")
        
        for case, result in test_results:
            logger.info(f"{case}: {result}")
        logger.info("=======================")

@pytest.mark.skipif(SKIP_CASE,reason='研发还需要优化，先跳过')
def test_HAND_FingerStart(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    finger_id_bits = 0x01
    remote_err = []
    err = serial_api_instance.HAND_FingerStart(HAND_ID, finger_id_bits, remote_err)
    assert err == HAND_RESP_SUCCESS, f"设置开始移动手指失败，错误码: err={err},remote_err={remote_err[0]}"
    logger.info(f'设置开始移动手指成功')
    
@pytest.mark.skipif(SKIP_CASE,reason='研发还需要优化，先跳过')
def test_HAND_FingerStop(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    finger_id_bits = 0x01
    remote_err = []
    err = serial_api_instance.HAND_FingerStop(HAND_ID, finger_id_bits, remote_err)
    assert err == HAND_RESP_SUCCESS, f"设置停止移动手指失败，错误码: err={err},remote_err={remote_err[0]}"
    logger.info(f'设置停止移动手指成功')
    
def get_FingerPosAbs(serial_api_instance,finger_id):
    delay_milli_seconds_impl(DELAY_MS*2)
    target_pos = [0]
    current_pos = [0]
    return serial_api_instance.HAND_GetFingerPosAbs(HAND_ID, finger_id, target_pos, current_pos, [])
    
@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_SetFingerPosAbs(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    DEFAULT_SPEED = 100  # 速度默认值（有效范围0-255）
    # 初始化存储校准数据的列表（长度匹配手指数量）
    # 定义测试常量
    end_pos = [0] * MAX_MOTOR_CNT
    start_pos = [0] * MAX_MOTOR_CNT
    motor_cnt = [MAX_MOTOR_CNT]
    thumb_root_pos = [0] * MAX_THUMB_ROOT_POS
    thumb_root_pos_cnt = [3]  # 初始请求3个拇指根位置数据
    # 获取每个手指的校准数据（列表类型，索引对应finger_id）
    delay_milli_seconds_impl(DELAY_MS)
    err, end_pos_get, start_pos_get, thumb_root_pos_get = serial_api_instance.HAND_GetCaliData(
        HAND_ID, end_pos, start_pos, motor_cnt, thumb_root_pos, thumb_root_pos_cnt, []
    )
    # 断言校准数据获取成功
    assert err == HAND_RESP_SUCCESS, f"获取校准数据失败: err={err}"
    logger.info(f"校准数据获取成功 | 各手指起始位置: {start_pos_get} | 各手指结束位置: {end_pos_get}")

    # -------------------------- 测试数据定义（按手指独立范围） --------------------------
    # 通用测试值（UINT16/UINT8边界+无效值）
    COMMON_POS_TEST = [
        (0, "绝对位置边界值(全局最小值)0"),
        (65535, "绝对位置边界值(全局最大值)65535"),
        (-1, "绝对位置无效值(负数)-1"),
        (65536, "绝对位置无效值(超UINT16上限)65536")
    ]
    COMMON_SPEED_TEST = [
        (0, "速度边界值(最小值)0"),
        (128, "速度中间值128"),
        (255, "速度边界值(最大值)255"),
        (-1, "速度无效值(负数)-1"),
        (256, "速度无效值(超UINT8上限)256")
    ]

    # 测试结果存储
    test_results = []

    try:
        """------------------- 按手指逐个测试（匹配自身校准范围） -------------------"""
        for finger_id in range(MAX_MOTOR_CNT):
            logger.info(f"\n===== 开始测试手指 {finger_id} 的绝对位置设置 =====")
            # 当前手指的校准位置范围
            finger_min_pos = start_pos_get[finger_id]
            finger_max_pos = end_pos_get[finger_id]
            logger.info(f"手指 {finger_id} 校准范围: 最小值={finger_min_pos} | 最大值={finger_max_pos}")

            # 构造当前手指的专属测试位置（包含自身校准范围+通用值）
            finger_pos_test = [
                (finger_min_pos, f"手指{finger_id}校准最小值{finger_min_pos}"),
                (finger_max_pos, f"手指{finger_id}校准最大值{finger_max_pos}"),
                ((finger_min_pos + finger_max_pos) // 2, f"手指{finger_id}校准中间值{(finger_min_pos + finger_max_pos) // 2}"),
                (finger_min_pos - 1, f"手指{finger_id}无效值(低于校准最小值){finger_min_pos - 1}"),
                (finger_max_pos + 1, f"手指{finger_id}无效值(高于校准最大值){finger_max_pos + 1}")
            ] + COMMON_POS_TEST

            # 1. 测试位置参数（固定速度为默认值）
            logger.info(f"测试手指 {finger_id} 的位置参数")
            for pos, desc in finger_pos_test:
                remote_err = []
                # 调用接口设置绝对位置
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerPosAbs(
                    HAND_ID, finger_id, 
                    pos,          # 测试位置值
                    DEFAULT_SPEED,  # 固定速度
                    remote_err
                )

                # 结果验证逻辑
                # 有效条件：1. 是UINT16类型 2. 在自身校准范围内
                is_pos_valid = (0 <= pos <= 65535)
                if is_pos_valid:
                    # 有效位置应返回成功
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效位置失败 | {desc} | err={err} | remote_err={remote_err[0] if remote_err else '无'}"
                    delay_milli_seconds_impl(DELAY_MS)
                    value = get_FingerPosAbs(serial_api_instance,finger_id)
                    assert value[0] == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 获取有效位置失败: {desc}, 错误码: err={err}"
                        
                    if pos < finger_min_pos:
                        assert abs(value[2] - finger_min_pos) < POS_MIN_LOSS, \
                                f"写入小于最小值{pos}(<{finger_min_pos})，但读取位置为{value[2]}（预期{finger_min_pos})"
                    elif pos > finger_max_pos:
                        assert abs(value[2] - finger_max_pos) < POS_MIN_LOSS, \
                                f"写入大于最大值{pos}(>{finger_max_pos})，但读取位置为{value[2]}（预期{finger_max_pos})"
                    else:
                        assert abs(value[2] - pos) < POS_MAX_LOSS, \
                            f"手指 {finger_id} 设置位置{pos}，读取位置{value[2]}，差值超出容差{POS_MAX_LOSS}"
                    test_results.append((f"手指{finger_id} 位置测试({desc})", "通过"))
                else:
                    # 无效位置应返回数据错误
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效位置未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} 位置测试({desc})", "通过(预期失败)"))

            # 2. 测试速度参数（固定位置为当前手指校准最小值）
            logger.info(f"测试手指 {finger_id} 的速度参数")
            for speed, desc in COMMON_SPEED_TEST:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerPosAbs(
                    HAND_ID, finger_id, 
                    finger_min_pos,  # 固定位置为当前手指校准最小值
                    speed,           # 测试速度值
                    remote_err
                )

                # 结果验证逻辑
                is_speed_valid = 0 <= speed <= 255
                if is_speed_valid:
                    # 有效速度应返回成功
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效速度失败 | {desc} | err={err} | remote_err={remote_err[0] if remote_err else '无'}"
                    test_results.append((f"手指{finger_id} 速度测试({desc})", "通过"))
                else:
                    # 无效速度应返回数据错误
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效速度未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} 速度测试({desc})", "通过(预期失败)"))

            logger.info(f"手指 {finger_id} 绝对位置设置测试完成")

        """------------------- 恢复所有手指到校准最小值 -------------------"""
        logger.info("\n===== 恢复所有手指到校准最小值 =====")
        for finger_id in range(MAX_MOTOR_CNT):
            remote_err = []
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetFingerPosAbs(
                HAND_ID, finger_id, 
                start_pos_get[finger_id], DEFAULT_SPEED,  # 恢复到校准最小值
                remote_err
            )
            assert err == HAND_RESP_SUCCESS, \
                f"恢复手指 {finger_id} 失败 | err={err} | remote_err={remote_err[0] if remote_err else '无'}"
            logger.info(f"手指 {finger_id} 已恢复到校准最小值: {start_pos_get[finger_id]}")

    except AssertionError as e:
        logger.error(f"测试失败: {str(e)}")
        raise  # 重新抛出错误，便于上层捕获

    finally:
        """------------------- 测试结果汇总 -------------------"""
        logger.info("\n===== 绝对位置设置测试结果汇总 =====")
        passed = sum(1 for case, result in test_results if "通过" in result)
        total = len(test_results)
        logger.info(f"总测试用例: {total} | 通过: {passed} | 失败: {total - passed}")
        # 打印每个用例结果
        for case, result in test_results:
            logger.info(f"{case}: {result}")
        logger.info("=======================")
    return test_results  # 返回测试结果，便于上层统计

def get_HAND_FingerPosAbsAll(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS*2)
    target_pos = [0] * MAX_MOTOR_CNT
    current_pos = [0] * MAX_MOTOR_CNT
    motor_cnt = [MAX_MOTOR_CNT]
    return serial_api_instance.HAND_GetFingerPosAbsAll(HAND_ID, target_pos, current_pos, motor_cnt, [])
    
@pytest.mark.skipif(SKIP_CASE,reason='超出范围值(校准范围)，不报无效值错误, 提bug:#5741,先跳过')
def test_HAND_SetFingerPosAbsAll(serial_api_instance):
    # 默认参数值
    delay_milli_seconds_impl(DELAY_MS_FUN)
    DEFAULT_POS = 0     # 位置默认值
    DEFAULT_SPEED = 100   # 速度默认值
    
    # 定义测试常量
    end_pos = [0] * MAX_MOTOR_CNT
    start_pos = [0] * MAX_MOTOR_CNT
    motor_cnt = [MAX_MOTOR_CNT]
    thumb_root_pos = [0] * MAX_THUMB_ROOT_POS
    thumb_root_pos_cnt = [3]  # 初始请求3个拇指根位置数据
    # 获取每个手指的校准数据（列表类型，索引对应finger_id）
    delay_milli_seconds_impl(DELAY_MS_FUN)
    err, end_pos_get, start_pos_get, thumb_root_pos_get = serial_api_instance.HAND_GetCaliData(
        HAND_ID, end_pos, start_pos, motor_cnt, thumb_root_pos, thumb_root_pos_cnt, []
    )
    # 增加断言，确保校准数据获取成功
    assert err == HAND_RESP_SUCCESS, f"获取校准数据失败: err={err}"
    logger.info(f'start_pos_get ={start_pos_get}')
    logger.info(f'end_pos_get ={end_pos_get}')
    temp_pos_end = end_pos_get
    
    # 定义各参数的测试值(包含有效/边界/无效值)
    PARAM_TEST_DATA = {
        'pos_abs_all': [
            (start_pos_get,       f"所有手指绝对位置最小值{start_pos_get}"),
            ([temp_pos_end[i] if i in (0, 5) else start_pos_get[i] for i in range(MAX_MOTOR_CNT)],          f"0、5手指绝对位置最大值（其余为0）"),
            ([temp_pos_end[i] if i in (1, 2,3,4) else start_pos_get[i] for i in range(MAX_MOTOR_CNT)],         f"1-4手指绝对位置最大值（其余为0）"),
            # 修复：无效的列表构造
            ([0]*MAX_MOTOR_CNT,      f"所有手指绝对位置边界值{[0]*MAX_MOTOR_CNT}"),
            ([65535,0,0,0,0,65535],      f"1,6手指绝对位置边界值[65535,0,0,0,0,65535]"),
            ([0,65535,65535,65535,65535,0],   f"2~4手指绝对位置边界值[0,65535,65535,65535,65535,0]"),
            ([-1]*MAX_MOTOR_CNT,     f"所有手指绝对位置边界值{[-1]*MAX_MOTOR_CNT}"),
            ([65536] * MAX_MOTOR_CNT,   "所有手指绝对位置边界值65536"),
        ],
        'speed': [
            ([0]*MAX_MOTOR_CNT,       "手指移动速度最小值0"),
            ([100]*MAX_MOTOR_CNT,     "手指移动速度中间值100"),
            ([255]*MAX_MOTOR_CNT,     "手指移动速度最大值255"),
            # 修复：无效的列表构造
            ([-1]*MAX_MOTOR_CNT,      "手指移动速度边界值-1"),
            ([256]*MAX_MOTOR_CNT,     "手指移动速度边界值256")
        ]
    }
    
    # 测试结果存储
    test_results = []
    
    try:
        """------------------- 单变量测试 -------------------"""
        logger.info(f"\n===== 开始批量设置手指绝对位置测试 =====")
        
        # 测试位置参数（固定速度为默认值）
        logger.info(f"测试位置参数")
        for idx, (pos, desc) in enumerate(PARAM_TEST_DATA['pos_abs_all'], start=0):
            speed_array = [DEFAULT_SPEED] * MAX_MOTOR_CNT
            remote_err = []
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetFingerPosAbsAll(
                HAND_ID, pos, speed_array, MAX_MOTOR_CNT, remote_err
            )
            
            # 修复：检查所有位置值的有效性
            is_all_pos_valid = all(
                0 <= pos[i] <= 65535 
                for i in range(len(pos))
            )
            
            if is_all_pos_valid:  # 所有手指的位置都在各自的有效范围
                assert err == HAND_RESP_SUCCESS, \
                    f"设置有效位置失败: {desc}, 错误码: err={err}, remote_err={remote_err[0] if remote_err else '无'}"
                delay_milli_seconds_impl(DELAY_MS)
                value = get_HAND_FingerPosAbsAll(serial_api_instance)
                assert value[0] == HAND_RESP_SUCCESS, \
                    f"获取有效位置失败, 错误码: err={err}"
                current_pos = value[2]  # 获取所有手指的当前位置列表 
                for i in range(MAX_MOTOR_CNT):
                    set_pos = pos[i]    # 第i个手指的设置值
                    read_pos = current_pos[i]  # 第i个手指的读取值
                    finger_min_pos = start_pos_get[i]
                    finger_max_pos = end_pos_get[i]
                    
                    if set_pos < finger_min_pos:
                        assert abs(read_pos - finger_min_pos) < POS_MIN_LOSS, \
                                f"第{i+1}指写入小于最小值{set_pos}(<{finger_min_pos})，读取值{read_pos}（预期{finger_min_pos})"
                        test_results.append((f"手指{i},位置测试({desc})", "通过"))
                    elif set_pos > finger_max_pos:
                        assert abs(read_pos - finger_max_pos) < POS_MIN_LOSS, \
                            f"第{i+1}指写入大于最大值{set_pos}(>{finger_max_pos})，读取值{read_pos}（预期{finger_max_pos})"
                        test_results.append((f"手指{i},位置测试({desc})", "通过"))
                    else:
                        assert abs(read_pos - set_pos) < POS_MAX_LOSS, \
                                f"第{i+1}指位置不一致 | 设置值:{set_pos}，读取值:{read_pos}，容差:{POS_MAX_LOSS}"
                        test_results.append((f"手指{i},位置测试({desc})", "不通过"))
                #恢复默认值，再进入下一轮测试
                err = serial_api_instance.HAND_SetFingerPosAbsAll(
                        HAND_ID, 
                        [DEFAULT_POS] * MAX_MOTOR_CNT,
                        [DEFAULT_SPEED] * MAX_MOTOR_CNT,
                        MAX_MOTOR_CNT,
                        remote_err)
                assert err == HAND_RESP_SUCCESS, \
                f"恢复默认位置失败, 错误码: err={err}, remote_err={remote_err[0] if remote_err else '无'}"
                delay_milli_seconds_impl(DELAY_MS)
            else:
                    # 无效位置应返回数据错误
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指设置无效位置未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指位置测试({desc})", "通过(预期失败)"))
        
        # 测试速度参数（固定位置为默认值）
        logger.info(f"测试速度参数")
        for speed, desc in PARAM_TEST_DATA['speed']:
            pos_array = [DEFAULT_POS] * MAX_MOTOR_CNT
            remote_err = []
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetFingerPosAbsAll(
                HAND_ID, pos_array, speed, MAX_MOTOR_CNT, remote_err
            )
            
            # 同样，建议检查所有速度值的有效性
            is_all_speed_valid = all(0 <= s <= 255 for s in speed)
            if is_all_speed_valid:  # 有效速度范围
                assert err == HAND_RESP_SUCCESS, \
                    f"设置有效速度失败: {desc}, 错误码: err={err}, remote_err={remote_err[0] if remote_err else '无'}"
                test_results.append((f"速度测试({desc})", "通过"))
            else:  # 无效速度值
                assert err != HAND_RESP_SUCCESS, \
                    f"设置无效速度未报错: {desc}, 错误码: err={err}, remote_err={remote_err[0] if remote_err else '无'}"
                test_results.append((f"速度测试({desc})", "通过(预期失败)"))
        
        logger.info(f"批量设置手指绝对位置测试完成")
        
        """------------------- 恢复默认值 -------------------"""
        logger.info("\n===== 恢复所有手指默认位置 =====")
        remote_err = []
        delay_milli_seconds_impl(DELAY_MS)
        err = serial_api_instance.HAND_SetFingerPosAbsAll(
            HAND_ID, 
            [DEFAULT_POS] * MAX_MOTOR_CNT,
            [DEFAULT_SPEED] * MAX_MOTOR_CNT,
            MAX_MOTOR_CNT,
            remote_err
        )
        assert err == HAND_RESP_SUCCESS, \
            f"恢复默认位置失败, 错误码: err={err}, remote_err={remote_err[0] if remote_err else '无'}"
        logger.info(f"所有手指已恢复默认位置: {DEFAULT_POS}, 速度: {DEFAULT_SPEED}")
    
    except AssertionError as e:
        logger.error(f"测试失败: {str(e)}")
        raise  # 重新抛出原始错误
    
    finally:
        """------------------- 测试结果汇总 -------------------"""
        logger.info("\n===== 批量设置手指绝对位置测试结果汇总 =====")
        passed = sum(1 for case, result in test_results if "通过" in result)
        total = len(test_results)
        logger.info(f"总测试用例: {total}, 通过: {passed}, 失败: {total - passed}")
        
        for case, result in test_results:
            logger.info(f"{case}: {result}")
        logger.info("=======================")

def get_HAND_FingerPos(serial_api_instance,finger_id):
    delay_milli_seconds_impl(DELAY_MS*2)
    target_pos = [0]
    current_pos = [0]
    return serial_api_instance.HAND_GetFingerPos(HAND_ID, finger_id, target_pos, current_pos, [])

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_SetFingerPos(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    # 默认参数值
    DEFAULT_POS = 0     # 位置默认值
    SIXTH_FINGER_MIN_POS = 728  # 第六指最小值
    DEFAULT_SPEED = 100   # 速度默认值32767
    # 定义各参数的测试值(包含有效/边界/无效值)
    PARAM_TEST_DATA = {
        'pos': [
            (0,       "手指逻辑位置最小值0"),
            (32767,   "手指逻辑位置中间值32767"),
            (65535,   "手指逻辑位置最大值65535"),
            (-1,      "手指逻辑位置边界值-1"),
            (65536,   "手指逻辑位置边界值65536")
        ],
        'speed': [
            (0,       "手指移动速度最小值0"),
            (100,     "手指移动速度中间值100"),
            (255,     "手指移动速度最大值255"),
            (-1,      "手指移动速度边界值-1"),
            (256,     "手指移动速度边界值256")
        ]
    }
    
    # 测试结果存储
    test_results = []
    
    try:
        """------------------- 单变量测试 -------------------"""
        for finger_id in range(MAX_MOTOR_CNT):
            logger.info(f"\n===== 开始测试手指 {finger_id} 的相对位置设置 =====")
            
            # 测试位置参数（固定速度为默认值）
            logger.info(f"测试手指 {finger_id} 的位置参数")
            for pos, desc in PARAM_TEST_DATA['pos']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerPos(
                    HAND_ID, finger_id, 
                    pos,          # 测试变量位置值
                    DEFAULT_SPEED,  # 速度固定为默认值
                    remote_err
                )
                
                # 验证结果
                if 0 <= pos <= 65535:  # 有效位置范围
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效位置失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    # delay_milli_seconds_impl(DELAY_MS)
                    value = get_HAND_FingerPos(serial_api_instance,finger_id)
                    assert value[0] == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 获取有效位置失败: {desc}, 错误码: err={err}"
                    #第六个和手指最小值为728的情况需要考虑
                    # 分场景校验位置一致性
                    if finger_id == MAX_MOTOR_CNT-1:
                        # 第六指特殊逻辑：写入<728时，读取值应为728；否则校验与写入值一致
                        if pos < SIXTH_FINGER_MIN_POS:
                            assert value[2] == SIXTH_FINGER_MIN_POS, \
                                f"第六指写入小于最小值{pos}(<728)，但读取位置为{value[2]}（预期728）"
                        else:
                            assert abs(value[2] - pos) < POS_MAX_LOSS, \
                                f"第六指设置位置{pos}，读取位置{value[2]}，差值超出容差{POS_MAX_LOSS}"
                    else:
                        # 其他手指：常规容差校验
                        assert abs(value[2] - pos) < POS_MAX_LOSS, \
                            f"手指 {finger_id} 设置位置{pos}，读取位置{value[2]}，差值超出容差{POS_MAX_LOSS}" 
                    test_results.append((f"手指{finger_id} 位置测试({desc})", "通过"))
                else:  # 无效位置值
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效位置未报错: {desc}, 错误码: err={err},remote_err={remote_err}"
                    test_results.append((f"手指{finger_id} 位置测试({desc})", "通过(预期失败)"))
            
            # 测试速度参数（固定位置为默认值）
            logger.info(f"测试手指 {finger_id} 的速度参数")
            for speed, desc in PARAM_TEST_DATA['speed']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerPos(
                    HAND_ID, finger_id, 
                    DEFAULT_POS,  # 位置固定为默认值
                    speed,        # 测试变量速度值
                    remote_err
                )
                
                # 验证结果
                if 0 <= speed <= 255:  # 有效速度范围
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效速度失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} 速度测试({desc})", "通过"))
                else:  # 无效速度值
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效速度未报错: {desc}, 错误码: err={err},remote_err={remote_err}"
                    test_results.append((f"手指{finger_id} 速度测试({desc})", "通过(预期失败)"))
            
            logger.info(f"手指 {finger_id} 相对位置设置测试完成")
        
        """------------------- 恢复默认值 -------------------"""
        logger.info("\n===== 恢复所有手指的默认位置 =====")
        for finger_id in range(MAX_MOTOR_CNT):
            remote_err = []
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetFingerPos(
                HAND_ID, finger_id, 
                DEFAULT_POS, DEFAULT_SPEED,  # 恢复默认位置和速度
                remote_err
            )
            assert err == HAND_RESP_SUCCESS, \
                f"恢复手指 {finger_id} 默认位置失败, 错误码: err={err},remote_err={remote_err[0]}"
            logger.info(f"手指 {finger_id} 已恢复默认位置: {DEFAULT_POS}, 速度: {DEFAULT_SPEED}")
    
    except AssertionError as e:
        logger.error(f"测试失败: {str(e)}")
        raise  # 重新抛出原始错误
    
    finally:
        """------------------- 测试结果汇总 -------------------"""
        logger.info("\n===== 相对位置设置测试结果汇总 =====")
        passed = sum(1 for case, result in test_results if "通过" in result)
        total = len(test_results)
        logger.info(f"总测试用例: {total}, 通过: {passed}, 失败: {total - passed}")
        
        for case, result in test_results:
            logger.info(f"{case}: {result}")
        logger.info("=======================")
        
def get_FingerPosAll(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS*2)
    target_pos = [0] * MAX_MOTOR_CNT
    current_pos = [0] * MAX_MOTOR_CNT
    motor_cnt = [MAX_MOTOR_CNT]
    remote_err = []
    return serial_api_instance.HAND_GetFingerPosAll(HAND_ID, target_pos, current_pos, motor_cnt, remote_err)
  
@pytest.mark.skipif(SKIP_CASE,reason='超出范围值，不报无效值错误')
def test_HAND_SetFingerPosAll(serial_api_instance):
    # 定义测试常量
    # 默认参数值
    delay_milli_seconds_impl(DELAY_MS_FUN)
    DEFAULT_POS = 0     # 位置默认值
    DEFAULT_SPEED = 100   # 速度默认值
    SIXTH_FINGER_MIN_POS = 728 # 第六指硬件最小值
    # 定义各参数的测试值(包含有效/边界/无效值)
    PARAM_TEST_DATA = {
        'pos_all': [
            ([0]*MAX_MOTOR_CNT,      f"所有手指绝对位置边界值{[0]*MAX_MOTOR_CNT}"),
            ([65535,0,0,0,0,65535],      f"1,6手指绝对位置边界值[65535,0,0,0,0,65535]"),
            ([32767,0,0,0,0,32767],      f"1,6手指绝对位置中间值[32767,0,0,0,0,32767]"),
            ([0,32767,32767,32767,32767,0],   f"2~4手指绝对位置中间值[0,32767,32767,32767,32767,0]"),
            ([0,65535,65535,65535,65535,0],   f"2~4手指绝对位置边界值[0,65535,65535,65535,65535,0]"),
             # 修复：无效的列表构造
            ([-1]*MAX_MOTOR_CNT,     f"所有手指绝对位置边界值{[-1]*MAX_MOTOR_CNT}"),
            ([65536] * MAX_MOTOR_CNT,   "所有手指绝对位置边界值65536"),
        ],
       'speed': [
            ([0]*MAX_MOTOR_CNT,       "手指移动速度最小值0"),
            ([100]*MAX_MOTOR_CNT,     "手指移动速度中间值100"),
            ([255]*MAX_MOTOR_CNT,     "手指移动速度最大值255"),
            # 修复：无效的列表构造
            ([-1]*MAX_MOTOR_CNT,      "手指移动速度边界值-1"),
            ([256]*MAX_MOTOR_CNT,     "手指移动速度边界值256")
        ]
    }
    
    # 测试结果存储
    test_results = []
    
    try:
        """------------------- 单变量测试 -------------------"""
        logger.info(f"\n===== 开始批量设置手指相对位置测试 =====")
        
        # 测试位置参数（固定速度为默认值）
        logger.info(f"测试位置参数")
        for pos, desc in PARAM_TEST_DATA['pos_all']:
            # 生成统一位置数组
            speed_array = [DEFAULT_SPEED] * MAX_MOTOR_CNT
            remote_err = []
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetFingerPosAll(
                HAND_ID, pos, speed_array, MAX_MOTOR_CNT, remote_err
            )
            
            # 验证结果
            is_all_pos_valid = all(
                0 <= pos[i] <= 65535 
                for i in range(len(pos))
            )
            if is_all_pos_valid:  # 有效位置范围
                assert err == HAND_RESP_SUCCESS, \
                    f"设置有效位置失败: {desc}, 错误码:err={err},remote_err={remote_err[0]}"
                # delay_milli_seconds_impl(DELAY_MS)
                # 批量位置设置后的校验逻辑
                value = get_FingerPosAll(serial_api_instance)
                # 1. 校验获取位置接口调用成功
                assert value[0] == HAND_RESP_SUCCESS, \
                    f"批量获取所有手指位置失败 | 错误码: err={value[0]}"  # 修正：错误码取value[0]而非err
                current_pos = value[2]  # 获取所有手指的当前位置列表

                # 2. 逐手指校验位置一致性（兼容第六指特殊逻辑）
                for i in range(MAX_MOTOR_CNT):
                    set_pos = pos[i]    # 第i个手指的设置值
                    read_pos = current_pos[i]  # 第i个手指的读取值
                    
                    # 处理第六指特殊规则：写入<728时，读取值必须为728
                    if i == MAX_MOTOR_CNT-1:
                        if set_pos < SIXTH_FINGER_MIN_POS:
                            assert read_pos == SIXTH_FINGER_MIN_POS, \
                                f"第{MAX_MOTOR_CNT}指（第六指）异常 | 设置值:{set_pos}(<728)，读取值:{read_pos}（预期728）"
                        else:
                            # 第六指写入≥728时，按容差校验
                            assert abs(read_pos - set_pos) < POS_MAX_LOSS, \
                                f"第{MAX_MOTOR_CNT}指（第六指）位置不一致 | 设置值:{set_pos}，读取值:{read_pos}，容差:{POS_MAX_LOSS}"
                    else:
                        # 其他手指：常规容差校验
                        assert abs(read_pos - set_pos) < POS_MAX_LOSS, \
                            f"第{i+1}指位置不一致 | 设置值:{set_pos}，读取值:{read_pos}，容差:{POS_MAX_LOSS}"
                # 3. 所有手指校验通过后记录结果
                test_results.append((f"批量位置测试({desc})", "通过"))
            else:  # 无效位置值
                assert err != HAND_RESP_SUCCESS, \
                    f"设置无效位置未报错: {desc}, 错误码: err={err},remote_err={remote_err}"
                test_results.append((f"位置测试({desc})", "通过(预期失败)"))
        
        # 测试速度参数（固定位置为默认值）
        logger.info(f"测试速度参数")
        for speed, desc in PARAM_TEST_DATA['speed']:
            # 生成统一速度数组
            pos_array = [DEFAULT_POS] * MAX_MOTOR_CNT
            remote_err = []
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetFingerPosAll(
                HAND_ID, pos_array, speed, MAX_MOTOR_CNT, remote_err
            )
            
            # 验证结果
            is_all_speed_valid = all(0 <= s <= 255 for s in speed)
            if is_all_speed_valid:  # 有效速度范围
                assert err == HAND_RESP_SUCCESS, \
                    f"设置有效速度失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                test_results.append((f"速度测试({desc})", "通过"))
            else:  # 无效速度值
                assert err != HAND_RESP_SUCCESS, \
                    f"设置无效速度未报错: {desc}, 错误码: err={err},remote_err={remote_err}"
                test_results.append((f"速度测试({desc})", "通过(预期失败)"))
        
        logger.info(f"批量设置手指相对位置测试完成")
        
        """------------------- 恢复默认值 -------------------"""
        logger.info("\n===== 恢复所有手指默认位置 =====")
        remote_err = []
        delay_milli_seconds_impl(DELAY_MS)
        err = serial_api_instance.HAND_SetFingerPosAll(
            HAND_ID, 
            [DEFAULT_POS] * MAX_MOTOR_CNT,
            [DEFAULT_SPEED] * MAX_MOTOR_CNT,
            MAX_MOTOR_CNT,
            remote_err
        )
        assert err == HAND_RESP_SUCCESS, \
            f"恢复默认位置失败, 错误码: err={err},remote_err={remote_err[0]}"
        logger.info(f"所有手指已恢复默认位置: {DEFAULT_POS}, 速度: {DEFAULT_SPEED}")
    
    except AssertionError as e:
        logger.error(f"测试失败: {str(e)}")
        raise  # 重新抛出原始错误
    
    finally:
        """------------------- 测试结果汇总 -------------------"""
        logger.info("\n===== 批量设置手指相对位置测试结果汇总 =====")
        passed = sum(1 for case, result in test_results if "通过" in result)
        total = len(test_results)
        logger.info(f"总测试用例: {total}, 通过: {passed}, 失败: {total - passed}")
        
        for case, result in test_results:
            logger.info(f"{case}: {result}")
        logger.info("=======================")

def get_angle_range(serial_api_instance, finger_id=0):
    """
    测试获取指定手指的实际角度极值范围（使用单手指API）
    :param serial_api_instance: 串口API实例
    :param finger_id: 要测试的手指ID（0~5）
    :return: 指定手指的实际最小值, 指定手指的实际最大值
    """
    delay_milli_seconds_impl(DELAY_MS*2)
    # 核心常量定义
    SPEED = 100
    ANGLE_MIN_THEORY = -32768  # 理论最小值
    ANGLE_MAX_THEORY = 32767   # 理论最大值
    
    # 1. 校验手指ID合法性
    if not isinstance(finger_id, int) or finger_id < 0 or finger_id >= MAX_MOTOR_CNT:
        raise ValueError(f"手指ID非法，必须是0~{MAX_MOTOR_CNT-1}之间的整数，当前值：{finger_id}")

    try:
        # 2. 设置指定手指到理论最小值，读取实际生效的最小值
        set_min_err = serial_api_instance.HAND_SetFingerAngle(
            HAND_ID, finger_id, ANGLE_MIN_THEORY, SPEED, []
        )
        assert set_min_err == HAND_RESP_SUCCESS, f"设置手指{finger_id}最小值失败，错误码：{set_min_err}"
        delay_milli_seconds_impl(DELAY_MS)

        target_angle_min = [0]
        current_angle_min = [0]
        read_min_result = serial_api_instance.HAND_GetFingerAngle(HAND_ID, finger_id, target_angle_min, current_angle_min, [])
        read_min_err = read_min_result[0]
        assert read_min_err == HAND_RESP_SUCCESS, f"读取手指{finger_id}最小值失败，错误码：{read_min_err}"
        finger_min_val = current_angle_min[0]

        # 3. 设置指定手指到理论最大值，读取实际生效的最大值
        delay_milli_seconds_impl(DELAY_MS)
        set_max_err = serial_api_instance.HAND_SetFingerAngle(HAND_ID, finger_id, ANGLE_MAX_THEORY, SPEED, [])
        assert set_max_err == HAND_RESP_SUCCESS, f"设置手指{finger_id}最大值失败，错误码：{set_max_err}"
        delay_milli_seconds_impl(DELAY_MS)

        target_angle_max = [0]
        current_angle_max = [0]
        delay_milli_seconds_impl(DELAY_MS)
        read_max_result = serial_api_instance.HAND_GetFingerAngle(HAND_ID, finger_id, target_angle_max, current_angle_max, [])
        read_max_err = read_max_result[0]
        assert read_max_err == HAND_RESP_SUCCESS, f"读取手指{finger_id}最大值失败，错误码：{read_max_err}"
        finger_max_val = current_angle_max[0]

        # 4. 校验极值合理性
        assert finger_min_val <= finger_max_val, f"手指{finger_id}极值异常：最小{finger_min_val} > 最大{finger_max_val}"
        
        # 5. 测试完成后恢复（按规则：第六指恢复最小值，其他恢复最大值）
        delay_milli_seconds_impl(DELAY_MS)
        recover_angle = finger_min_val if finger_id == 5 else finger_max_val
        recover_err = serial_api_instance.HAND_SetFingerAngle(HAND_ID, finger_id, recover_angle, SPEED, [])
        assert recover_err == HAND_RESP_SUCCESS, f"恢复手指{finger_id}失败，错误码：{recover_err}"

        return finger_min_val, finger_max_val

    except AssertionError as e:
        logger.info(f"获取手指{finger_id}极值失败：{str(e)}")
        raise
    except Exception as e:
        logger.info(f"获取手指{finger_id}极值异常：{str(e)}")
        raise

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_SetFingerAngle(serial_api_instance):    
    delay_milli_seconds_impl(DELAY_MS_FUN)
    # 核心常量
    DEFAULT_SPEED = 100
    # 逐个获取每个手指的实际极值
    actual_angle_min = []
    actual_angle_max = []
    for finger_id in range(MAX_MOTOR_CNT):
        finger_min, finger_max = get_angle_range(serial_api_instance, finger_id)
        actual_angle_min.append(finger_min)
        actual_angle_max.append(finger_max)
    logger.info(f'actual_angle_min = {actual_angle_min}')
    logger.info(f'actual_angle_max = {actual_angle_max}')
    # 构造测试用例
    angle_test_cases = []
    for finger_id in range(MAX_MOTOR_CNT):
            finger_min = actual_angle_min[finger_id]
            finger_max = actual_angle_max[finger_id]
            finger_mid = (finger_min + finger_max) // 2  # 计算当前手指的中间值
            angle_test_cases.extend([
                (-32768, f"手指{finger_id}-理论最小值-32768"),
                (finger_min, f"手指{finger_id}-实际最小值"),
                (finger_mid, f"手指{finger_id}-实际中间值({finger_mid})"),
                (finger_max, f"手指{finger_id}-实际最大值"),
                (32767, f"手指{finger_id}-理论最大值32767"),
            ])

    test_results = []

    try:
        # 单手指独立测试
        for finger_id in range(MAX_MOTOR_CNT):
            finger_min = actual_angle_min[finger_id]
            finger_max = actual_angle_max[finger_id]

            # 测试角度参数
            for angle, desc in angle_test_cases:
                delay_milli_seconds_impl(DELAY_MS)
                # 设置角度
                set_err = serial_api_instance.HAND_SetFingerAngle(HAND_ID, finger_id, angle, DEFAULT_SPEED, [])
                assert set_err == HAND_RESP_SUCCESS, f"手指{finger_id}设置角度{angle}失败，错误码:{set_err}"

                # 读取角度
                target_angle = [0]
                current_angle = [0]
                delay_milli_seconds_impl(DELAY_MS)
                read_result = serial_api_instance.HAND_GetFingerAngle(HAND_ID, finger_id, target_angle, current_angle, [])
                read_err = read_result[0]
                current_angle_val = read_result[2]
                assert read_err == HAND_RESP_SUCCESS, f"手指{finger_id}读取角度失败，错误码:{read_err}"

                # 验证逻辑（严格匹配：超界钳位到极值，区间内误差≤100）
                if angle < finger_min:  # 写入值小于最小值 → 读取值必须等于最小值
                    angle_diff = abs(current_angle_val-finger_min)
                    assert angle_diff <= FINGER_ANGLE_TARGET_MIN_LOSS, \
                        f"手指{finger_id}超最小值失败：写入{angle}(<{finger_min}), 实际读取{current_angle_val}≠{finger_min}"
                    test_results.append((f"手指{finger_id}({desc})", "通过(超最小值)"))
                elif angle > finger_max:  # 写入值大于最大值 → 读取值必须等于最大值
                    angle_diff = abs(current_angle_val-finger_max)
                    assert angle_diff <= FINGER_ANGLE_TARGET_MIN_LOSS, \
                        f"手指{finger_id}超最大值失败：写入{angle}(>{finger_max}), 实际读取{current_angle_val}≠{finger_max}"
                    test_results.append((f"手指{finger_id}({desc})", "通过(超最大值)"))
                elif finger_min <= angle <= finger_max:  # 写入值在区间内 → 误差≤100
                    angle_diff = abs(current_angle_val - angle)
                    assert angle_diff <= FINGER_ANGLE_TARGET_MAX_LOSS, \
                        f"手指{finger_id}角度误差超限：写入{angle}, 实际{current_angle_val}, 误差{angle_diff}>{FINGER_ANGLE_TARGET_MAX_LOSS}"
                    test_results.append((f"手指{finger_id}({desc})", f"通过(区间内误差{angle_diff})"))
                    
            delay_milli_seconds_impl(DELAY_MS)
            # 测试完成后恢复：第六指恢复最小值，其他恢复最大值
            recover_angle = finger_min if finger_id == 5 else finger_max
            recover_err = serial_api_instance.HAND_SetFingerAngle(HAND_ID, finger_id, recover_angle, DEFAULT_SPEED, [])
            assert recover_err == HAND_RESP_SUCCESS, f"恢复手指{finger_id}失败，错误码:{recover_err}"
         
    except AssertionError as e:
        logger.info(f"测试失败: {str(e)}")
        raise
    finally:
        # 结果汇总
        logger.info("\n===== 测试结果汇总 =====")
        passed = sum(1 for _, res in test_results if "通过" in res)
        total = len(test_results)
        logger.info(f"总用例: {total}, 通过: {passed}, 失败: {total - passed}")
        for case, res in test_results:
            logger.info(f"{case}: {res}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中,先跳过')
def test_HAND_SetFingerAngleAll(serial_api_instance):
    """批量设置所有手指角度测试（严格遵循分组默认值规则）"""
    delay_milli_seconds_impl(DELAY_MS_FUN)
    # 核心常量（对齐单手指验收用例）
    DEFAULT_SPEED = 100
    # 1. 预获取所有手指实际极值 + 记录初始值（用于恢复）
    actual_angle_min = []
    actual_angle_max = []
    finger_init_vals = []  # 记录每个手指测试前的初始值
    for finger_id in range(MAX_MOTOR_CNT):
        finger_min, finger_max = get_angle_range(serial_api_instance, finger_id)
        actual_angle_min.append(finger_min)
        actual_angle_max.append(finger_max)
        # 读取并记录当前手指的初始值（用于后续恢复）
        target_angle = [0]
        current_angle = [0]
        delay_milli_seconds_impl(DELAY_MS)
        read_res = serial_api_instance.HAND_GetFingerAngle(HAND_ID, finger_id, target_angle, current_angle, [])
        finger_init_vals.append(read_res[2])
    logger.info(f'actual_angle_min = {actual_angle_min}')
    logger.info(f'actual_angle_max = {actual_angle_max}')
    logger.info(f'手指初始值 = {finger_init_vals}')

    # 2. 构造测试用例（复用单手指用例结构）
    angle_test_cases = []
    for finger_id in range(MAX_MOTOR_CNT):
        finger_min = actual_angle_min[finger_id]
        finger_max = actual_angle_max[finger_id]
        finger_mid = (finger_min + finger_max) // 2
        angle_test_cases.extend([
            (-32768, f"手指{finger_id}-理论最小值-32768"),
            (finger_min, f"手指{finger_id}-实际最小值"),
            (finger_mid, f"手指{finger_id}-实际中间值({finger_mid})"),
            (finger_max, f"手指{finger_id}-实际最大值"),
            (32767, f"手指{finger_id}-理论最大值32767"),
        ])

    test_results = []
    # 定义测试分组（明确ID对应关系）
    test_groups = [
        (0,  "1指(ID0)"),
        ([1,2,3,4], "2-5指(ID1-4)"),
        (5,  "6指(ID5)")
    ]

    try:
        logger.info("\n开始批量设置手指角度测试（严格遵循分组默认值规则）")
        # 分组测试（精准控制默认值写入 + 仅恢复测试手指）
        for target_fid, group_name in test_groups:
            logger.info(f"\n开始测试 {group_name}")
            # 统一转换为列表，简化后续判断
            target_fids = [target_fid] if isinstance(target_fid, int) else target_fid

            for angle, case_desc in angle_test_cases:
                delay_milli_seconds_impl(DELAY_MS)
                # 构造批量角度数组（严格匹配默认值规则）
                angle_array = []
                for fid in range(MAX_MOTOR_CNT):
                    if fid in target_fids:
                        # 目标手指写入测试值
                        angle_array.append(angle)
                    else:
                        # 非目标手指写入默认值（1-5指最小值，6指最大值）
                        angle_array.append(actual_angle_min[fid] if fid == 5 else actual_angle_max[fid])
                
                speed_array = [DEFAULT_SPEED] * MAX_MOTOR_CNT
                remote_err = []

                # 执行批量设置
                delay_milli_seconds_impl(DELAY_MS)
                logger.info(f"angle_array = {angle_array}")
                set_err = serial_api_instance.HAND_SetFingerAngleAll(
                    HAND_ID, angle_array, speed_array, MAX_MOTOR_CNT, remote_err
                )

                # 验证批量设置成功
                case_label = f"{group_name}-{case_desc}({angle})"
                assert set_err == HAND_RESP_SUCCESS, \
                    f"{case_label} 批量设置失败，错误码={set_err}，远程错误={remote_err[0] if remote_err else '无'}"
                
                # 校验目标手指角度（复用单手指验收通过的规则）
                for fid in target_fids:
                    target_angle = [0]
                    current_angle = [0]
                    delay_milli_seconds_impl(DELAY_MS)
                    read_res = serial_api_instance.HAND_GetFingerAngle(HAND_ID, fid, target_angle, current_angle, [])
                    read_err = read_res[0]
                    curr_val = read_res[2]
                    assert read_err == HAND_RESP_SUCCESS, f"{case_label} 读取{fid+1}指角度失败，错误码={read_err}"

                    # 误差判断（对齐单手指验收逻辑）
                    finger_min = actual_angle_min[fid]
                    finger_max = actual_angle_max[fid]
                    if angle < finger_min:
                        angle_diff = abs(curr_val - finger_min)
                        assert angle_diff <= FINGER_ANGLE_TARGET_MIN_LOSS, \
                            f"{case_label} {fid+1}指超最小值失败：写入{angle}(<{finger_min}), 实际{curr_val}，误差{angle_diff}>{FINGER_ANGLE_TARGET_MIN_LOSS}"
                        test_results.append((case_label, "通过(超最小值)"))
                    elif angle > finger_max:
                        angle_diff = abs(curr_val - finger_max)
                        assert angle_diff <= FINGER_ANGLE_TARGET_MIN_LOSS, \
                            f"{case_label} {fid+1}指超最大值失败：写入{angle}(>{finger_max}), 实际{curr_val}，误差{angle_diff}>{FINGER_ANGLE_TARGET_MIN_LOSS}"
                        test_results.append((case_label, "通过(超最大值)"))
                    else:
                        angle_diff = abs(curr_val - angle)
                        assert angle_diff <= FINGER_ANGLE_TARGET_MAX_LOSS, \
                            f"{case_label} {fid+1}指误差超限：写入{angle}, 实际{curr_val}, 误差{angle_diff}>{FINGER_ANGLE_TARGET_MAX_LOSS}"
                        test_results.append((case_label, f"通过(区间内误差{angle_diff})"))

                # ========== 核心修改：仅恢复测试的手指到原值，其他手指值不变 ==========
                for fid in target_fids:
                    # 恢复测试手指到测试前的初始值
                    init_val = finger_init_vals[fid]
                    delay_milli_seconds_impl(DELAY_MS)
                    serial_api_instance.HAND_SetFingerAngle(HAND_ID, fid, init_val, DEFAULT_SPEED, [])
                logger.info(f"{case_label} 验证完成，仅恢复测试手指({target_fids})到初始值，其他手指值不变")

            logger.info(f"{group_name} 所有用例测试完成")

    except AssertionError as e:
        logger.info(f"测试失败: {str(e)}")
        raise
    finally:
        logger.info("\n===== 测试结果汇总 =====")
        passed = sum(1 for _, res in test_results if "通过" in res)
        total = len(test_results)
        logger.info(f"总用例: {total}, 通过: {passed}, 失败: {total - passed}")
        for case, res in test_results:
            logger.info(f"{case}: {res}")
            
def get_HAND_ThumbRootPos(serial_api_instance):
    raw_encoder = [0]
    pos = [0]
    return serial_api_instance.HAND_GetThumbRootPos(HAND_ID, raw_encoder, pos, [])

@pytest.mark.skipif(SKIP_CASE,reason='超出范围值(0,1,2)，在0~255之间的异常值无法检测出来,提bug:#5742,先跳过')
def test_HAND_SetThumbRootPos(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    # 定义测试常量
    # 默认参数值
    DEFAULT_POS = 1     # 位置默认值（合法值：0, 1, 2）
    DEFAULT_SPEED = 100   # 速度默认值（范围：0-255）
    # 定义各参数的测试值(包含有效/边界/无效值)
    PARAM_TEST_DATA = {
        'thumb_root_pos': [
            (0,     "旋转大拇指到预设位置值0"),
            (1,     "旋转大拇指到预设位置值1"),
            (2,     "旋转大拇指到预设位置值2"),
            (-1,    "旋转大拇指到预设位置边界值-1"),
            (255,     "旋转大拇指到预设位置边界值255"),
            (256,     "旋转大拇指到预设位置边界值256")
        ],
        'speed': [
            (0,       "手指移动速度最小值0"),
            (100,     "手指移动速度中间值100"),
            (255,     "手指移动速度最大值255"),
            (-1,      "手指移动速度边界值-1"),
            (256,     "手指移动速度边界值256")
        ]
    }
    
    # 测试结果存储
    test_results = []
    
    try:
        """------------------- 单变量测试 -------------------"""
        logger.info(f"\n===== 开始测试拇指根部位置设置 =====")
        
        # 测试位置参数（固定速度为默认值）
        logger.info(f"测试拇指根部位置参数")
        for pos, desc in PARAM_TEST_DATA['thumb_root_pos']:
            remote_err = []
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetThumbRootPos(
                HAND_ID, 
                pos,              # 测试变量位置值
                DEFAULT_SPEED,    # 速度固定为默认值
                remote_err
            )
            
            # 验证结果
            if pos in [0, 1, 2]:  # 有效位置范围
                assert err == HAND_RESP_SUCCESS, \
                    f"设置拇指根部有效位置失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                delay_milli_seconds_impl(DELAY_MS)
                value = get_HAND_ThumbRootPos(serial_api_instance)
                assert value[0] == HAND_RESP_SUCCESS, \
                    f"获取拇指根部有效位置失败, 错误码: err={err}"
                assert pos == value[2], \
                    f"获取拇指根部有效位置{value[2]}, 与设置的有效位置{pos}不匹配"
                test_results.append((f"拇指根部位置测试({desc})", "通过"))
            else:  # 无效位置值
                assert err != HAND_RESP_SUCCESS, \
                    f"设置拇指根部无效位置未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                test_results.append((f"拇指根部位置测试({desc})", "通过(预期失败)"))
        
        # 测试速度参数（固定位置为默认值）
        logger.info(f"测试拇指根部速度参数")
        for speed, desc in PARAM_TEST_DATA['speed']:
            remote_err = []
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetThumbRootPos(
                HAND_ID, 
                DEFAULT_POS,      # 位置固定为默认值
                speed,            # 测试变量速度值
                remote_err
            )
            
            # 验证结果
            if 0 <= speed <= 255:  # 有效速度范围
                assert err == HAND_RESP_SUCCESS, \
                    f"设置拇指根部有效速度失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                test_results.append((f"拇指根部速度测试({desc})", "通过"))
            else:  # 无效速度值
                assert err != HAND_RESP_SUCCESS, \
                    f"设置拇指根部无效速度未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                test_results.append((f"拇指根部速度测试({desc})", "通过(预期失败)"))
        
        logger.info(f"拇指根部位置设置测试完成")
        
        """------------------- 恢复默认值 -------------------"""
        logger.info("\n===== 恢复拇指根部默认位置 =====")
        remote_err = []
        delay_milli_seconds_impl(DELAY_MS)
        err = serial_api_instance.HAND_SetThumbRootPos(
            HAND_ID, 
            DEFAULT_POS, DEFAULT_SPEED,  # 恢复默认位置和速度
            remote_err
        )
        assert err == HAND_RESP_SUCCESS, \
            f"恢复拇指根部默认位置失败, 错误码: err={err},remote_err={remote_err[0]}"
        logger.info(f"拇指根部已恢复默认位置: {DEFAULT_POS}, 速度: {DEFAULT_SPEED}")
    
    except AssertionError as e:
        logger.error(f"测试失败: {str(e)}")
        raise  # 重新抛出原始错误
    
    finally:
        """------------------- 测试结果汇总 -------------------"""
        logger.info("\n===== 拇指根部位置设置测试结果汇总 =====")
        passed = sum(1 for case, result in test_results if "通过" in result)
        total = len(test_results)
        logger.info(f"总测试用例: {total}, 通过: {passed}, 失败: {total - passed}")
        
        for case, result in test_results:
            logger.info(f"{case}: {result}")
        logger.info("=======================")
        
@pytest.mark.skipif(SKIP_CASE,reason='置多个手指的正常值，报无效值错误，提bug：#5723，先跳过')
def test_HAND_SetFingerForcePID(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
        # 默认参数值
    DEFAULT_P = 250.00
    DEFAULT_I = 2.00
    DEFAULT_D = 250.00
    DEFAULT_G = 1.00
    # 定义各参数的测试值(包含有效/边界/无效值)
    PARAM_TEST_DATA = {
        'P': [
            (1.00,   "P值最小值1.00"),
            (240.00, "P值中间值240.00"),
            (500.00, "P值最大值500.00"),
            (0.90,    "P值边界值0.9"),
            (0.00,     "P值边界值0.00"),
            (-1.00,    "P值边界值-1.00"),
            (501.00, "P值边界值501.00"),
            (65535.00, "P值边界值65535.00"),
            (65536.00, "P值边界值65536.00")
        ],
        'I': [
            (0.00,     "I值最小值0.00"),
            (50.00,  "I值中间值50.00"),
            (100.00, "I值最大值100.00"),
            (-1.00,    "I值边界值-1.00"),
            (101.00, "I值边界值101.00"),
            (65535.00, "I值边界值65535.00"),
            (65536.00, "I值边界值65536.00")
        ],
        'D': [
            (0.00,     "D值最小值0.00"),
            (240.00, "D值中间值240.00"),
            (500.00, "D值最大值500.00"),
            (-1.00,    "D值边界值-1.00"),
            (501.00, "D值边界值501.00"),
            (65535.00, "D值边界值65535.00"),
            (65536.00, "D值边界值65536.00")
        ],
        'G': [
            (0.01,     "G值最小值0.01"),
            (0.50,    "G值中间值0.50"),
            (1.00,   "G值最大值1.00"),
            (0.00,     "G值边界值0.00"),
            (-1.00,    "G值边界值-1.00"),
            (1.05,   "G值边界值1.05"),
            (65535.00, "G值边界值65535.00"),
            (65536.00, "G值边界值65536.00")
        ]
    }
    
    # 测试结果存储
    test_results = []
    
    try:
        """------------------- 单变量测试 -------------------"""
        for finger_id in range(MAX_MOTOR_CNT-1):
            logger.info(f"\n===== 开始测试手指 {finger_id} 的力控PID参数 =====")
            
            # 测试P参数
            logger.info(f"测试手指 {finger_id} 的P参数")
            for p_value, desc in PARAM_TEST_DATA['P']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerForcePID(
                    HAND_ID, finger_id, 
                    p_value,        # 测试变量P
                    DEFAULT_I,      # I固定为默认值
                    DEFAULT_D,      # D固定为默认值
                    DEFAULT_G,      # G固定为默认值
                    remote_err
                )
                
                # 验证结果
                if 1.00 <= p_value <= 500.00:  # 有效P值范围
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效P值失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    delay_milli_seconds_impl(DELAY_MS)
                    value = get_HAND_FORCE_PID(serial_api_instance,finger_id)
                    assert value[0] == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 获取有效P值失败: {desc}, 错误码: err={err}"
                    assert abs(p_value - value[1]) < PID_MAX_LOSS, \
                        f"手指 {finger_id} 设置的P值: {p_value}, 与读取的P值:{value[1]}不一致"
                    test_results.append((f"手指{finger_id} P值测试({desc})", "通过"))
                else:  # 无效P值
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效P值未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} P值测试({desc})", "通过(预期失败)"))
            
            # 测试I参数
            logger.info(f"测试手指 {finger_id} 的I参数")
            for i_value, desc in PARAM_TEST_DATA['I']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerForcePID(
                    HAND_ID, finger_id, 
                    DEFAULT_P,      # P固定为默认值
                    i_value,        # 测试变量I
                    DEFAULT_D,      # D固定为默认值
                    DEFAULT_G,      # G固定为默认值
                    remote_err
                )
                
                # 验证结果
                if 0.00 <= i_value <= 100.00:  # 有效I值范围
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效I值失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    delay_milli_seconds_impl(DELAY_MS)
                    value = get_HAND_FORCE_PID(serial_api_instance,finger_id)
                    assert value[0] == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 获取有效I值失败: {desc}, 错误码: err={err}"
                    assert abs(i_value - value[2]) < PID_MAX_LOSS, \
                        f"手指 {finger_id} 设置的I值: {i_value}, 与读取的I值:{value[2]}不一致"
                    test_results.append((f"手指{finger_id} I值测试({desc})", "通过"))
                else:  # 无效I值
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效I值未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} I值测试({desc})", "通过(预期失败)"))
            
            # 测试D参数
            logger.info(f"测试手指 {finger_id} 的D参数")
            for d_value, desc in PARAM_TEST_DATA['D']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerForcePID(
                    HAND_ID, finger_id, 
                    DEFAULT_P,      # P固定为默认值
                    DEFAULT_I,      # I固定为默认值
                    d_value,        # 测试变量D
                    DEFAULT_G,      # G固定为默认值
                    remote_err
                )
                
                # 验证结果
                if 0.00 <= d_value <= 500.00:  # 有效D值范围
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效D值失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    delay_milli_seconds_impl(DELAY_MS)
                    value = get_HAND_FORCE_PID(serial_api_instance,finger_id)
                    assert value[0] == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 获取有效D值失败: {desc}, 错误码: err={err}"
                    assert abs(d_value - value[3]) < PID_MAX_LOSS, \
                        f"手指 {finger_id} 设置的D值: {d_value}, 与读取的D值:{value[3]}不一致"
                    test_results.append((f"手指{finger_id} D值测试({desc})", "通过"))
                else:  # 无效D值
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效D值未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} D值测试({desc})", "通过(预期失败)"))
            
            # 测试G参数
            logger.info(f"测试手指 {finger_id} 的G参数")
            for g_value, desc in PARAM_TEST_DATA['G']:
                remote_err = []
                delay_milli_seconds_impl(DELAY_MS)
                err = serial_api_instance.HAND_SetFingerForcePID(
                    HAND_ID, finger_id, 
                    DEFAULT_P,      # P固定为默认值
                    DEFAULT_I,      # I固定为默认值
                    DEFAULT_D,      # D固定为默认值
                    g_value,        # 测试变量G
                    remote_err
                )
                
                # 验证结果
                if 0.01 <= g_value <= 1.00:  # 有效G值范围
                    assert err == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置有效G值失败: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    delay_milli_seconds_impl(DELAY_MS)
                    value = get_HAND_FORCE_PID(serial_api_instance,finger_id)
                    assert value[0] == HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 获取有效G值失败: {desc}, 错误码: err={err}"
                    assert abs(g_value - value[4]) < PID_MAX_LOSS, \
                        f"手指 {finger_id} 设置的G值: {g_value}, 与读取的G值:{value[4]}不一致"
                    test_results.append((f"手指{finger_id} G值测试({desc})", "通过"))
                else:  # 无效G值
                    assert err != HAND_RESP_SUCCESS, \
                        f"手指 {finger_id} 设置无效G值未报错: {desc}, 错误码: err={err},remote_err={remote_err[0]}"
                    test_results.append((f"手指{finger_id} G值测试({desc})", "通过(预期失败)"))
            
            logger.info(f"手指 {finger_id} 的力控PID参数测试完成")
        
        """------------------- 恢复默认值 -------------------"""
        logger.info("\n===== 恢复所有手指的默认力控PID参数 =====")
        for finger_id in range(MAX_MOTOR_CNT-1):
            remote_err = []
            delay_milli_seconds_impl(DELAY_MS)
            err = serial_api_instance.HAND_SetFingerForcePID(
                HAND_ID, finger_id, 
                DEFAULT_P, DEFAULT_I, DEFAULT_D, DEFAULT_G, remote_err
            )
            assert err == HAND_RESP_SUCCESS, \
                f"恢复手指 {finger_id} 默认力控PID参数失败, 错误码: err={err},remote_err={remote_err[0]}"
            logger.info(f"手指 {finger_id} 已恢复默认力控PID参数")
    
    except AssertionError as e:
        logger.error(f"测试失败: {str(e)}")
        raise  # 重新抛出原始错误
    
    finally:
        """------------------- 测试结果汇总 -------------------"""
        logger.info("\n===== 力控PID参数测试结果汇总 =====")
        passed = sum(1 for case, result in test_results if "通过" in result)
        total = len(test_results)
        logger.info(f"总测试用例: {total}, 通过: {passed}, 失败: {total - passed}")
        
        for case, result in test_results:
            logger.info(f"{case}: {result}")
        logger.info("=======================")
        
@pytest.mark.skipif(SKIP_CASE,reason='debug中，先跳过')
def test_HAND_ResetForce(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    remote_err = []
    err = serial_api_instance.HAND_ResetForce(HAND_ID, remote_err)
    assert err == HAND_RESP_SUCCESS, f"重置力量值，错误码: err={err},remote_err={remote_err[0]}"
    logger.info("成功重置力量值")

@pytest.mark.skipif(SKIP_CASE,reason='debug中，先跳过')
def test_HAND_SetSelfTestLevel(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    SELF_TEST_LEVEL = {
        '等待指令': 0,
        '半自检': 1,
        '完整自检': 2
    }
    
    # 测试设置为半自检
    remote_err = [0]
    err = serial_api_instance.HAND_SetSelfTestLevel(HAND_ID, SELF_TEST_LEVEL['半自检'], remote_err)
    assert err == HAND_RESP_SUCCESS, f"设置半自检失败，错误码: err={err},remote_err={remote_err[0]}"
    
    delay_milli_seconds_impl(DELAY_MS*2)
    
    current_level = [0]
    err,_ = serial_api_instance.HAND_GetSelfTestLevel(HAND_ID, current_level, [])
    assert err == HAND_RESP_SUCCESS, f"获取自检级别失败，错误码: err={err},remote_err={remote_err[0]}"
    
    assert current_level[0] == SELF_TEST_LEVEL['半自检'], (
        f"自检级别验证失败：期望半自检({SELF_TEST_LEVEL['半自检']})，"
        f"实际{list(SELF_TEST_LEVEL.keys())[list(SELF_TEST_LEVEL.values()).index(current_level[0])]}({current_level[0]})"
    )
    logger.info("成功设置半自检")
    
    delay_milli_seconds_impl(DELAY_MS*2)
    # 测试设置为完整自检（恢复默认状态）
    remote_err = []
    err = serial_api_instance.HAND_SetSelfTestLevel(HAND_ID, SELF_TEST_LEVEL['完整自检'], remote_err)
    assert err == HAND_RESP_SUCCESS, f"设置完整自检失败，错误码: err={err},remote_err={remote_err[0]}"
    delay_milli_seconds_impl(DELAY_MS*2) # 等待自检执行
    
    delay_milli_seconds_impl(DELAY_MS*2)
    err,_ = serial_api_instance.HAND_GetSelfTestLevel(HAND_ID, current_level, [])
    assert err == HAND_RESP_SUCCESS, f"获取自检级别失败，错误码:err={err}"
    
    assert current_level[0] == SELF_TEST_LEVEL['完整自检'], (
        f"自检级别验证失败：期望完整自检({SELF_TEST_LEVEL['完整自检']})，"
        f"实际{list(SELF_TEST_LEVEL.keys())[list(SELF_TEST_LEVEL.values()).index(current_level[0])]}({current_level[0]})"
    )
    logger.info("成功设置完整自检")
    
    delay_milli_seconds_impl(DELAY_MS*2)
    # 确保测试结束后恢复默认状态
    remote_err = [0]
    err = serial_api_instance.HAND_SetSelfTestLevel(HAND_ID, SELF_TEST_LEVEL['完整自检'], remote_err)
    if err != HAND_RESP_SUCCESS:
        logger.error(f"恢复默认自检级别失败，错误码: err={err},remote_err={remote_err[0]}")

@pytest.mark.skipif(SKIP_CASE,reason='debug中，先跳过')
def test_HAND_SetBeepSwitch(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    BEEP_STATUS = {
        'OFF': 0,
        'ON': 1
    }
   
    # 测试关闭蜂鸣器
    err = serial_api_instance.HAND_SetBeepSwitch(HAND_ID, BEEP_STATUS['OFF'], [])
    assert err == HAND_RESP_SUCCESS, f"设置蜂鸣器关闭失败，错误码: err={err}"
    
    delay_milli_seconds_impl(DELAY_MS)
    
    status_container = [0]
    err,_ = serial_api_instance.HAND_GetBeepSwitch(HAND_ID, status_container, [])
    assert err == HAND_RESP_SUCCESS, f"获取蜂鸣器状态失败，错误码: err={err}"
    
    actual_status = status_container[0]
    assert actual_status == BEEP_STATUS['OFF'], (
        f"蜂鸣器关闭状态验证失败：期望={BEEP_STATUS['OFF']}，实际={actual_status}"
    )
    logger.info("蜂鸣器已成功关闭")
    
    delay_milli_seconds_impl(DELAY_MS)
    # 测试开启蜂鸣器
    err = serial_api_instance.HAND_SetBeepSwitch(HAND_ID, BEEP_STATUS['ON'], [])
    assert err == HAND_RESP_SUCCESS, f"设置蜂鸣器开启失败，错误码: err={err}"
    
    delay_milli_seconds_impl(DELAY_MS)
    
    err,_ = serial_api_instance.HAND_GetBeepSwitch(HAND_ID, status_container, [])
    assert err == HAND_RESP_SUCCESS, f"获取蜂鸣器状态失败，错误码: err={err}"
    
    actual_status = status_container[0]
    assert actual_status == BEEP_STATUS['ON'], (
        f"蜂鸣器开启状态验证失败：期望={BEEP_STATUS['ON']}，实际={actual_status}"
    )
    logger.info("蜂鸣器已成功开启")
    
    delay_milli_seconds_impl(DELAY_MS)
    # 恢复默认状态
    err = serial_api_instance.HAND_SetBeepSwitch(HAND_ID, BEEP_STATUS['ON'], [])
    if err != HAND_RESP_SUCCESS:
        logger.error(f"恢复蜂鸣器默认状态失败，错误码: err={err}")
    else:
        logger.info('蜂鸣器开关已恢复默认状态')

@pytest.mark.skipif(SKIP_CASE,reason='debug中，先跳过')
def test_HAND_Beep(serial_api_instance): 
    delay_milli_seconds_impl(DELAY_MS_FUN)
    duration = 500
    err = serial_api_instance.HAND_Beep(HAND_ID, duration, [])
    assert err == HAND_RESP_SUCCESS,f"设置蜂鸣器时长失败:  err={err}"
    logger.info(f'成功设置蜂鸣器时长：{duration}')
    
@pytest.mark.skipif(True,reason='按钮不支持,此case暂时跳过')
def test_HAND_SetButtonPressedCnt(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    # 测试正常范围（0-255）
    # 测试最小值
    target_pressed_cnt = 0
    remote_err = []
    delay_milli_seconds_impl(DELAY_MS)
    err = serial_api_instance.HAND_SetButtonPressedCnt(HAND_ID, target_pressed_cnt, remote_err)
    assert err == HAND_RESP_SUCCESS, (
        f"设置按钮按下次数失败（值={target_pressed_cnt}），错误码:  err={err},remote_err={remote_err[0]}"
    )
    
    observed_pressed_cnt = [0]
    delay_milli_seconds_impl(DELAY_MS)
    err = serial_api_instance.HAND_GetButtonPressedCnt(HAND_ID, observed_pressed_cnt, remote_err)
    assert err == HAND_RESP_SUCCESS, (
        f"获取按钮按下次数失败（值={target_pressed_cnt}），错误码:  err={err},remote_err={remote_err[0]}"
    )
    
    actual_cnt = observed_pressed_cnt[0]
    assert actual_cnt == target_pressed_cnt, (
        f"按钮按下次数验证失败：目标值={target_pressed_cnt}，实际值={actual_cnt}"
    )
    
    logger.info(f"按钮按下次数设置成功，值={target_pressed_cnt}")
    
    # 测试中间值
    target_pressed_cnt = 128
    remote_err = []
    delay_milli_seconds_impl(DELAY_MS)
    err = serial_api_instance.HAND_SetButtonPressedCnt(HAND_ID, target_pressed_cnt, remote_err)
    assert err == HAND_RESP_SUCCESS, (
        f"设置按钮按下次数失败（值={target_pressed_cnt}），错误码: err={err},remote_err={remote_err[0]}"
    )
    
    observed_pressed_cnt = [0]
    delay_milli_seconds_impl(DELAY_MS)
    err = serial_api_instance.HAND_GetButtonPressedCnt(HAND_ID, observed_pressed_cnt, remote_err)
    assert err == HAND_RESP_SUCCESS, (
        f"获取按钮按下次数失败（值={target_pressed_cnt}），错误码: err={err},remote_err={remote_err[0]}"
    )
    
    actual_cnt = observed_pressed_cnt[0]
    assert actual_cnt == target_pressed_cnt, (
        f"按钮按下次数验证失败：目标值={target_pressed_cnt}，实际值={actual_cnt}"
    )
    
    logger.info(f"按钮按下次数设置成功，值={target_pressed_cnt}")
    
    # 测试最大值
    target_pressed_cnt = 255
    remote_err = []
    delay_milli_seconds_impl(DELAY_MS)
    err = serial_api_instance.HAND_SetButtonPressedCnt(HAND_ID, target_pressed_cnt, remote_err)
    assert err == HAND_RESP_SUCCESS, (
        f"设置按钮按下次数失败（值={target_pressed_cnt}），错误码: err={err},remote_err={remote_err[0]}"
    )
    
    observed_pressed_cnt = [0]
    delay_milli_seconds_impl(DELAY_MS)
    err = serial_api_instance.HAND_GetButtonPressedCnt(HAND_ID, observed_pressed_cnt, remote_err)
    assert err == HAND_RESP_SUCCESS, (
        f"获取按钮按下次数失败（值={target_pressed_cnt}），错误码:err={err},remote_err={remote_err[0]}"
    )
    
    actual_cnt = observed_pressed_cnt[0]
    assert actual_cnt == target_pressed_cnt, (
        f"按钮按下次数验证失败：目标值={target_pressed_cnt}，实际值={actual_cnt}"
    )
    
    logger.info(f"按钮按下次数设置成功，值={target_pressed_cnt}")
    
    # 测试超出范围（256-65535） - 期望触发ValueError
    # 测试超出范围的最小值（256）
    try:
        delay_milli_seconds_impl(DELAY_MS)
        serial_api_instance.HAND_SetButtonPressedCnt(HAND_ID, 256, [0])
    except ValueError as e:
        logger.info(f"成功捕获预期的ValueError（值=256）: {str(e)}")
    else:
        assert False, "设置超出范围的值（256）未触发ValueError"
    
    # 测试中间值（32768）
    try:
        delay_milli_seconds_impl(DELAY_MS)
        serial_api_instance.HAND_SetButtonPressedCnt(HAND_ID, 32768, [0])
    except ValueError as e:
        logger.info(f"成功捕获预期的ValueError（值=32768）: {str(e)}")
    else:
        assert False, "设置超出范围的值（32768）未触发ValueError"
    
    # 测试超出范围的最大值（65535）
    try:
        delay_milli_seconds_impl(DELAY_MS)
        serial_api_instance.HAND_SetButtonPressedCnt(HAND_ID, 65535, [0])
    except ValueError as e:
        logger.info(f"成功捕获预期的ValueError（值=65535）: {str(e)}")
    else:
        assert False, "设置超出范围的值（65535）未触发ValueError"
    
    # 测试负数（-1）
    try:
        delay_milli_seconds_impl(DELAY_MS)
        serial_api_instance.HAND_SetButtonPressedCnt(HAND_ID, -1, [0])
    except ValueError as e:
        logger.info(f"成功捕获预期的ValueError（值=-1）: {str(e)}")
    else:
        assert False, "设置负数（-1）未触发ValueError"

@pytest.mark.skipif(SKIP_CASE,reason='debug中，先眺过')
def test_HAND_StartInit(serial_api_instance):
    delay_milli_seconds_impl(DELAY_MS_FUN)
    remote_err = []
    err = serial_api_instance.HAND_StartInit(HAND_ID, remote_err)
    assert err == HAND_RESP_SUCCESS,f"初始化手失败，错误码: 错误码:err={err},remote_err={remote_err[0]}"
    logger.info(f'手初始化成功')
    delay_milli_seconds_impl(DELAY_MS_FUN*2)
    
    logger.info(f'恢复默认自检级别')
    remote_err = [0]
    err = serial_api_instance.HAND_SetSelfTestLevel(HAND_ID, 2, remote_err)
    if err != HAND_RESP_SUCCESS:
        logger.error(f"恢复默认自检级别失败，错误码: err={err},remote_err={remote_err[0]}")
    
