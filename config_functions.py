import os
import cv2

def get_channel_ranges():
    channel_ranges = {
        'IN1': range(0, 16),
        'IN2': range(16, 32),
        'IN3': range(32, 48),
        'IN4': range(48, 64),
        'IN5': range(64, 80),
        'IN6': range(80, 96),
        'IN7': range(96, 112),
        'IN8': range(112, 128),
        'MULT_IN1': range(128, 192),
        'MULT_IN2': range(192, 256),
        'MULT_IN3': range(256, 320),
        'MULT_IN4': range(320, 384),
        'AUX_IN1': range(384, 385),
        'AUX_IN2': range(385, 386),
        'AUX_IN3': range(386, 387),
        'AUX_IN4': range(387, 388),
        'AUX_IN5': range(388, 389),
        'AUX_IN6': range(389, 390),
        'AUX_IN7': range(390, 391),
        'AUX_IN8': range(391, 392),
        'AUX_IN9': range(392, 393),
        'AUX_IN10': range(393, 394),
        'AUX_IN11': range(394, 395),
        'AUX_IN12': range(395, 396),
        'AUX_IN13': range(396, 397),
        'AUX_IN14': range(397, 398),
        'AUX_IN15': range(398, 399),
        'AUX_IN16': range(399, 400),
    }
    return channel_ranges


def select_channels(inputs):
    if not isinstance(inputs, list) or not all(isinstance(item, str) for item in inputs):
        raise TypeError("La entrada debe ser una lista de strings.")

    channel_ranges = get_channel_ranges()
    channels_to_plot = []
    invalid_inputs = []
    for input_string in inputs:
        if input_string in channel_ranges:
            channels_to_plot.extend(channel_ranges[input_string])
        else:
            invalid_inputs.append(input_string)
    if invalid_inputs:
        valid_inputs = ", ".join(channel_ranges.keys())
        raise ValueError(f"Los siguientes inputs no son válidos: {', '.join(invalid_inputs)}. Las opciones válidas son: {valid_inputs}.")
    return channels_to_plot


def get_channel_name(channel_number):
    channel_ranges = get_channel_ranges()
    for key, rng in channel_ranges.items():
        if channel_number in rng:
            if 'AUX' in key:
                return key  # AUX_IN channels have no subindex
            else:
                sub_index = channel_number - rng.start + 1
                return f"{key} - {sub_index}"
    return "Unknown Channel"


def create_input_config(used_inputs):
    inputs = {}
    byte_inputs = {}
    configurable_inputs = ['IN1', 'IN2', 'IN3', 'IN4', 'IN5', 'IN6', 'IN7', 'IN8', 'MULT_IN1', 'MULT_IN2', 'MULT_IN3', 'MULT_IN4']
    for input_num in used_inputs:
        if input_num in configurable_inputs:
            inputs[input_num] = {
                'sensor': 0,
                'adapter': 0,
                'high_pass_filter': 0.7,
                'low_pass_filter': 130,
                'mode': 'Monopolar'
            }
            byte_inputs[input_num] = {
                'byte1': '00000000',
                'byte2': '00000000'
            }
    return inputs, byte_inputs


def input_config(inputs, used_input, sensor, adapter, high_pass_filter, low_pass_filter, mode):
    list_sensors = list(range(24))
    list_adapters = list(range(7))
    list_high_pass_filter = [0.7, 10, 100, 200]
    list_low_pass_filter = [130, 500, 900, 4400]
    list_mode = ['Monopolar', 'Differential', 'Bipolar']
    if used_input in inputs:
        if sensor in list_sensors:
            inputs[used_input]['sensor'] = sensor
        else:
            raise ValueError(f"{sensor} is not a valid sensor.\n Valid sensors are: {list_sensors}")
        if adapter in list_adapters:
            inputs[used_input]['adapter'] = adapter
        else:
            raise ValueError(f"{adapter} is not a valid adapter.\n Valid adapters are: {list_adapters}")
        if high_pass_filter in list_high_pass_filter:
            inputs[used_input]['high_pass_filter'] = high_pass_filter
        else:
            raise ValueError(f"{high_pass_filter} is not a valid high-pass filter value.\n Valid values are: {list_high_pass_filter}")
        if low_pass_filter in list_low_pass_filter:
            inputs[used_input]['low_pass_filter'] = low_pass_filter
        else:
            raise ValueError(f"{low_pass_filter} is not a valid low-pass filter value. \n Valid values are: {list_low_pass_filter}")
        if mode in list_mode:
            inputs[used_input]['mode'] = mode
        else:
            raise ValueError(f"{mode} is not a valid mode. \n Valid modes are: {list_mode}")
    else:
        raise ValueError(f"Input {used_input} not in use")


def config_to_byte(inputs, byte_inputs):
    for key in inputs:
        binary_sensor = bin(inputs[key]['sensor'])[2:].zfill(5)
        binary_adapter = bin(inputs[key]['adapter'])[2:].zfill(3)
        byte_inputs[key]['byte1'] = binary_sensor + binary_adapter

        binary_hpf = hpf_to_bits(inputs[key]['high_pass_filter'])
        binary_lpf = lpf_to_bits(inputs[key]['low_pass_filter'])
        binary_mode = mode_to_bits(inputs[key]['mode'])
        byte_inputs[key]['byte2'] = '00' + binary_hpf + binary_lpf + binary_mode

    return byte_inputs


def hpf_to_bits(hpf):
    if hpf == 0.7:
        binary_hpf = '00'
    elif hpf == 10:
        binary_hpf = '01'
    elif hpf == 100:
        binary_hpf = '10'
    elif hpf == 200:
        binary_hpf = '11'
    return binary_hpf


def lpf_to_bits(lpf):
    if lpf == 130:
        binary_lpf = '00'
    elif lpf == 500:
        binary_lpf = '01'
    elif lpf == 900:
        binary_lpf = '10'
    elif lpf == 4400:
        binary_lpf = '11'
    return binary_lpf


def mode_to_bits(mode):
    if mode == 'Monopolar':
        binary_mode = '00'
    elif mode == 'Differential':
        binary_mode = '01'
    elif mode == 'Bipolar':
        binary_mode = '10'
    return binary_mode


def get_available_filename(base_name, extension):
    counter = 0
    while True:
        if counter == 0:
            filename = f"{base_name}.{extension}"
        else:
            filename = f"{base_name}{counter}.{extension}"
        if not os.path.exists(filename):
            return filename, counter
        counter += 1


def get_number_filename(base_name, extension, number):
    if number == 0:
        filename = f"{base_name}.{extension}"
        return filename
    else:
        filename = f"{base_name}{number}.{extension}"
        return filename


def get_landmark_name(landmark_num):
    lm_names = ['NOSE', 'LEFT_EYE_IN', 'LEFT_EYE', 'LEFT_EYE_OUT', 'RIGHT_EYE_IN', 'RIGTH_EYE', 'RIGHT_EYE_OUT',
                'LEFT_EAR', 'RIGHT_EAR', 'MOUTH_LEFT', 'MOUTH_RIGHT', 'LEFT_SHOULDER', 'RIGHT_SHOULDER', 'LEFT_ELBOW',
                'RIGHT_ELBOW', 'LEFT_WRIST', 'RIGHT_WRIST', 'LEFT_PINKY', 'RIGHT_PINKY', 'LEFT_INDEX', 'RIGHT_INDEX',
                'LEFT_THUMB', 'RIGHT_THUMB', 'LEFT_HIP', 'RIGHT_HIP', 'LEFT_KNEE', 'RIGHT_KNEE', 'LEFT_ANKLE', 'RIGHT_ANKLE',
                'LEFT_HEEL', 'RIGHT_HEEL', 'LEFT_FOOT_INDEX', 'RIGHT_FOOT_INDEX']
    return lm_names[landmark_num]


def create_video(number):
    # Check if output.avi already exists
    # file_exists = os.path.isfile("videos/video.avi")
    # if not file_exists:
    #     filename = "videos/video.avi"
    #     output = cv2.VideoWriter(
    #         filename, cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))
    if number == 0:
        filename = "videos/video.avi"
        output = cv2.VideoWriter(
            filename, cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))
    else:
        filename = f"videos/video{number}.avi"
        output = cv2.VideoWriter(
            filename, cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))

    return output, filename


def trim_matrix(matrix, data_interval):
    num_rows, num_columns = matrix.shape

    # Iterate through the matrix in steps of 68
    for i in range(0, num_rows, data_interval):
        if matrix[i, 0] > -0.5:
            threshold = i // data_interval - 1  # Threshold package
            if threshold < 0:
                threshold = 0  # Ensure threshold is not negative
            threshold_row = threshold * data_interval
            trimmed_matrix = matrix[threshold_row:]
            return trimmed_matrix, threshold
    return matrix, 0


if __name__ == '__main__':
    pass
