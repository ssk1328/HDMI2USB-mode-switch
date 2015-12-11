
# A) Discover an unconfigured Cypress FX2 chip

# Board(dev=device, type="opsis", state="unconfigured")

# B) Program the Opsis EEPROM with information
# B1) Load FX2 chip with EEPROM firmware
# B2) Read the EEPROM information
# B3) Generate an EEPROM configuration
# B4) Program the EEPROM with the details
# B5) Reboot the board, discover a Cypress FX2 in "unconfigured mode"
# B6) Load the FX2 chip with EEPROM firmware
# B7) Read the EEPROM information and check

# C) Run the firmware tests from Ankit
# C1) Load the FX2 chip with ixo-usb-jtag firmware
# C2) Load the "test" firmware onto the FPGA
# C3) Load the FX2 chip with CDC-serial
# C4) Do the tests


# D) Load the SPI flash with demo firmware
# D1) Load the FX2 chip with ixo-usb-jtag firmware
# D2) Load the fpga with the SPI flash proxy
# D3) Download the firmware into the SPI flash
# D4) Reboot the board
# D5) Check the 


# E) Generate ID bar code
#  ) Read the EEPROM MAC Address
#  ) Read the Spartan 6 Device DNA
#  ) Read generate ID bar code from it

import hdmi2usb_boards

boards = find_boards()
assert len(boards) > 0, "No boards found."
assert len(boards) == 1, "Too many boards found."
assert boards[0].type == "opsis", "Opsis board not found."

# load_fx2


