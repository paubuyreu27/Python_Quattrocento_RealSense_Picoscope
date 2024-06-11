import config_functions as cf

#############################################################################
# AMPLIFIER SELECTION                                                       #
#############################################################################

used_amp = 'QUATTROCENTO'
ip_address = '169.254.1.10'
port = 23456

# SAMPLING FREQUENCY
sampling_frequency = 2048   # This value can be 512, 2048, 5120, 10240


#############################################################################
# PLOT OPTIONS                                                              #
#############################################################################

data_interval = 68   # Number of samples between camera frames --> 68 is highly recommended
samples_in_plot = 2041  # 2041 --> aprox. 1 second
max_channels_to_plot = 8
arbitrary_distance_plot_channels = 2# Forced distance between plots (mV)

#############################################################################
# PICOSCOPE OPTIONS                                                         #
#############################################################################

picoscope_shots = 100          # SHOTS FOR GEN. SQUARE SIGNAL
picoscope_frequency = 1         # FREQ. OF GEN. SIGNAL (HZ)
picoscope_pkToPk = 2000000      # micro-V

#############################################################################
# INPUT SELECTION                                                           #
#############################################################################

# POSSIBLE INPUTS (str):
# 'IN1', 'IN2', 'IN3', ... , 'IN8',
# 'MULT_IN1', 'MULT_IN2', ... , 'MULT_IN4',
# 'AUX_IN1', 'AUX_IN2', ... , 'AUX_IN16'

picoscope_input = ['AUX_IN1']   # USE AUXILIAR INPUT
list_used_inputs = []

list_used_inputs = picoscope_input + list_used_inputs
inputs_config, byte_config = cf.create_input_config(list_used_inputs)

#############################################################################
# CONFIGURATION FOR USED INPUT                                              #
# ATTENTION: only valid for IN and MULTIPLE_IN      not valid for AUX_IN    #
#############################################################################

# First input configuration
# used_input = 'MULT_IN1'  # Input to configure --> Copy string from list of used inputs
# sensor = 13  # Sensor used: see list in pdf.  Valid from 0 to 23
# adapter = 4  # Adapter used: see list in pdf.  Valid from 0 to 6
# high_pass_filter = 10  # High pass filter used. To choose between [0.7, 10, 100, 200] Hz
# low_pass_filter = 500  # Low pass filter used. To choose between [130, 500, 900, 4400] Hz
# mode = 'Monopolar'  # Mode used. String to choose between ['Monopolar', 'Differential', 'Bipolar']
# cf.input_config(inputs_config, used_input, sensor, adapter, high_pass_filter, low_pass_filter, mode)

# Second input configuration (comment all section if only one input configuration is wanted)
# used_input = 'IN1'  # Input to configure --> Copy string from list of used inputs
# sensor = 21  # Sensor used: see list in pdf.  Valid from 0 to 23
# adapter = 4  # Adapter used: see list in pdf.  Valid from 0 to 6
# high_pass_filter = 10  # High pass filter used. To choose between [0.7, 10, 100, 200] Hz
# low_pass_filter = 130  # Low pass filter used. To choose between [130, 500, 900, 4400] Hz
# mode = 'Monopolar'  # Mode used. String to choose between ['Monopolar', 'Differential', 'Bipolar']
# cf.input_config(inputs_config, used_input, sensor, adapter, high_pass_filter, low_pass_filter, mode)

# For each configurable input, copy and paste the structure above

# Send configuration to amplifier
byte_config = cf.config_to_byte(inputs_config, byte_config)

#######################################################################################################################
# Run file to check config on console
if __name__ == "__main__":
    print(f"You are using the amplifier {used_amp} with a sample frequency of {sampling_frequency}")
    print(f"Active inputs are {list_used_inputs}")
    print("Configuration of inputs (Auxiliary inputs not included):")
    for key, value in inputs_config.items():
        print(key + ": " + str(value))

