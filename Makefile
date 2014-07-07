SOURCES = main.c 

BUILD_DIR=build/

OPENCM3_DIR = libopencm3
LINK_SCRIPT= -T"$(OPENCM3_DIR)/lib/stm32/f1/stm32f100x6.ld"

C_INCLUDE_DIR=-I "$(OPENCM3_DIR)/include"
C_LIB_DIR=-L "$(OPENCM3_DIR)/lib"

TARGET_NAME=test1.bin
TOOLCHAIN=arm-none-eabi-

#We add the python files as depency for make so it detects when we change them
PYTHON_LIBS=stonerlights.py
C_LIBS=-lopencm3_stm32f1
#Generic stuff from here

DEPS=$(SOURCES:%.c=$(BUILD_DIR)%.d)
PRECOMPILED=$(SOURCES:%.c=$(BUILD_DIR)%.ipc)
OBJECTS=$(PRECOMPILED:%.ipc=%.o)


TARGET=$(BUILD_DIR)$(TARGET_NAME)

CC=$(TOOLCHAIN)gcc
OBJCOPY=$(TOOLCHAIN)objcopy
OBJDUMP=$(TOOLCHAIN)objdump
SIZETOOL=$(TOOLCHAIN)size
LD=$(TOOLCHAIN)ld

PYPROC=python test1.py

C_DEFS= -DSTM32F1
C_FLAGS= -Os -Wall -xc 
CPU= -mcpu=cortex-m3 -mthumb


LINK_FLAGS= --static -nostartfiles   $(C_LIB_DIR) $(C_LIBS)

print_size: all
	@echo 'Checking size: $@'
	$(SIZETOOL)  --format=berkeley "$(TARGET:.bin=.elf)"
	@echo ' '

upload: all
	stm32flash /dev/ttyUSB0 -b 1000000 -R cs.rts -B cs.dtr -w $(TARGET)

all: $(PYTHON_LIBS) $(SOURCES) $(TARGET)

print_debug:
	@echo Build target: $(TARGET)
	@echo
	@echo Sources: $(SOURCES)
	@echo
	@echo Dependency output: $(DEPS)
	@echo
	@echo Precompiled: $(PRECOMPILED)
	@echo
	@echo Processed by python: $(PYTHON_PROCESSED)
	@echo
	@echo Objects: $(OBJECTS)
	@echo



#$(TARGET): $(OBJECTS)
#	$(CC) $(OBJECTS) -o $@



$(PRECOMPILED): $(BUILD_DIR)%.ipc: %.c
	@echo 'Preprocessing file with $(PYPROC): $<'
	$(PYPROC) $< $@



$(OBJECTS): %.o: %.ipc
	@echo 'Building file: $<'
	$(CC) -std=gnu99 -Wa,-adhlns="$(@:.o=.lst)" -c -fmessage-length=0 -MMD -MP -MF"$(@:.o=.d)" -MT"$(@:.o=.d)" $(CPU) $(C_FLAGS) $(C_DEFS) $(C_INCLUDE_DIR) -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

$(TARGET:%.bin=%.elf): $(OBJECTS)
	@echo 'Building target: $@'
	$(CC) $(OBJECTS) $(LINK_FLAGS) $(LINK_SCRIPT) -Wl,-Map,"$(TARGET:.bin=.map)" -mcpu=cortex-m3 -mfix-cortex-m3-ldrd -mthumb -o "$(TARGET:.bin=.elf)" 
	@echo 'Finished building target: $@'
	@echo ' '

$(TARGET): $(TARGET:%.bin=%.elf)
	@echo 'Creating target: $@'
	$(OBJCOPY) -O binary "$(TARGET:.bin=.elf)" "$(TARGET)"
	@echo 'Finished building: $@'
	@echo ' '

$(TARGET:%.bin=%.lst): $(TARGET:%.bin=%.elf)
	@echo 'Create Listing: $@'
	$(OBJDUMP) -h -S "$(TARGET:.bin=.elf)" > "$(TARGET:.bin=.lst)"
	@echo 'Finished building: $@'
	@echo ' '



clean:
	rm -f $(PRECOMPILED) $(PYTHON_PROCESSED) $(OBJECTS) $(TARGET) $(TARGET:.bin=.elf) $(TARGET:.bin=.map) $(TARGET:.bin=.lst) $(OBJECTS:.o=.lst) $(OBJECTS:.o=.d) $(POSTPRECOMPILED)

#.PHONY: all clean target Makefile $(PYTHON_LIBS)
