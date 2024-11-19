from ttboard.demoboard import DemoBoard
from ttboard.mode import RPMode
from machine import Pin

REG_PC = 0
REG_SP = 1
REG_EXEC = 2
REG_STACK_TOP = 3


class SpellController:
    def __init__(self, tt: DemoBoard):
        self.tt = tt
        self.i_run = tt.inputs[0]
        self.i_step = tt.inputs[1]
        self.i_load = tt.inputs[2]
        self.i_dump = tt.inputs[3]
        self.i_shift_in = tt.inputs[4]
        self.i_reg_sel_0 = tt.inputs[5]
        self.i_reg_sel_1 = tt.inputs[6]

        self.o_cpu_sleep = tt.outputs[0]
        self.o_cpu_stop = tt.outputs[1]
        self.o_wait_delay = tt.outputs[2]
        self.o_shift_out = tt.outputs[3]

        self.i_run.off()
        self.i_step.off()
        self.i_load.off()
        self.i_dump.off()
        self.i_shift_in.off()
        self.i_reg_sel_0.off()
        self.i_reg_sel_1.off()

    def ensure_cpu_stopped(self):
        while self.o_cpu_stop._parent.value() == 0:
            self.tt.clock_project_once()

    def stopped(self):
        return self.o_cpu_stop._parent.value() == 0

    def sleeping(self):
        return self.o_cpu_stop._parent.value() == 1

    def set_reg_sel(self, value: int):
        self.i_reg_sel_0.value(value & 1)
        self.i_reg_sel_1.value((value >> 1) & 1)

    def write_reg(self, reg: int, value: int):
        for i in range(8):
            self.i_shift_in.value((value >> (7 - i)) & 1)
            self.tt.clock_project_once()
        self.set_reg_sel(reg)
        self.i_load.value(1)
        self.tt.clock_project_once()
        self.i_load.value(0)
        self.tt.clock_project_once()

    def read_reg(self, reg: int):
        self.set_reg_sel(reg)
        self.i_dump.value(1)
        self.tt.clock_project_once()
        self.i_dump.value(0)
        value = 0
        for i in range(8):
            self.tt.clock_project_once()
            value |= self.o_shift_out._parent.value() << (7 - i)
        return value

    def execute(self, wait=True):
        self.ensure_cpu_stopped()
        self.i_run.value(1)
        self.i_step.value(0)
        self.tt.clock_project_once()
        self.i_run.value(0)
        self.tt.clock_project_once()
        if wait:
            self.ensure_cpu_stopped()

    def single_step(self):
        self.ensure_cpu_stopped()
        self.i_run.value(1)
        self.i_step.value(1)
        self.tt.clock_project_once()
        self.i_step.value(0)
        self.i_run.value(0)
        self.tt.clock_project_once()
        self.ensure_cpu_stopped()

    def exec_opcode(self, opcode):
        int_opcode = ord(opcode) if type(opcode) == str else int(opcode)
        self.ensure_cpu_stopped()
        self.write_reg(REG_EXEC, int_opcode)
        self.ensure_cpu_stopped()

    def read_stack_top(self):
        return self.read_reg(REG_STACK_TOP)

    def push(self, value: int):
        self.ensure_cpu_stopped()
        self.write_reg(REG_STACK_TOP, value)

    def read_pc(self):
        return self.read_reg(REG_PC)

    def set_pc(self, value: int):
        self.write_reg(REG_PC, value)

    def read_sp(self):
        return self.read_reg(REG_SP)

    def set_sp(self, value: int):
        self.write_reg(REG_SP, value)

    def set_sp_read_stack(self, index: int):
        self.set_sp(index)
        return self.read_stack_top()

    def write_progmem(self, addr: int, value: Union[int, str]):
        """
        Writes a value to progmem by executing an instruction on the CPU.
        """
        int_value = ord(value) if type(value) == str else int(value)
        self.push(int_value)
        self.push(addr)
        self.exec_opcode("!")

    def write_program(self, opcodes, offset=0):
        for index, opcode in enumerate(opcodes):
            self.write_progmem(offset + index, opcode)


def run():
    tt = DemoBoard.get()
    tt.mode = RPMode.ASIC_RP_CONTROL
    tt.shuttle.tt_um_urish_spell.enable()
    spell = SpellController(tt)
    tt.reset_project(True)
    tt.clock_project_once()
    tt.reset_project(False)
    tt.pin_sdi_nprojectrst.init(mode=Pin.OUT, value=1)
    # fmt: off
    test_program = [
      127, 58, 119, 0, 129, 57, 57, 244, 62, 116, 109, 59, 119, 250,
      44, 0, 59, 119, 25, 44, 11, 64, 3, 61
    ]
    # fmt: on
    spell.write_program(test_program)
    print("Start")
    spell.execute(False)
    tt.clock_project_PWM(10_000_000)  # 10 MHz


run()
