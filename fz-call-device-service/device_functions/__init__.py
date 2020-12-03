import device_functions.fz_g_test_dev
import device_functions.fz_g_mq2
import device_functions.fz_g_light_sensor
import device_functions.fz_g_dht11

CALL_FUNCTIONS = {
    fz_g_test_dev.DEVICE_NAME: fz_g_test_dev.CALL_FUNCTION,
    fz_g_mq2.DEVICE_NAME: fz_g_mq2.CALL_FUNCTION,
    fz_g_light_sensor.DEVICE_NAME: fz_g_light_sensor.CALL_FUNCTION,
    fz_g_dht11.DEVICE_NAME: fz_g_dht11.CALL_FUNCTION
}


def get_call_device_function(device_name):
    if device_name in CALL_FUNCTIONS:
        return CALL_FUNCTIONS[device_name]
    else:
        raise Exception(
            "Call function of {} is not found.".format(device_name))
