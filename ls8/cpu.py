"""CPU functionality."""

import sys

# OPCODES - *from SPEC (these Values come from Steps 8 and on)
PRN = 0b01000111
LDI = 0b10000010
HLT = 0b00000001
MUL = 0b10100010
PUSH = 0b01000101
POP = 0b01000110
CALL = 0b01010000
RET = 0b00010001
ADD = 0b10100000 # need ADD bc of line 26 in call.ls8


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.pc = 0 # Program Counter -> points to currently-executing instruction
        self.branchtable = {} #comes from instructions in Step 9 to "beautify"
        self.branchtable[PRN] = self.handle_PRN
        self.branchtable[LDI] = self.handle_LDI
        self.branchtable[HLT] = self.handle_HLT
        self.branchtable[MUL] = self.handle_MUL
        self.branchtable[PUSH] = self.handle_PUSH
        self.branchtable[POP] = self.handle_POP
        self.branchtable[CALL] = self.handle_CALL
        self.branchtable[RET] = self.handle_RET
        self.branchtable[ADD] = self.handle_ADD
        self.SP = 7  # sets stack pointer to Register 7 *from SPEC
        self.stack_pointer = self.reg[self.SP] = 244 # sets to DEC equivalent of F4 // The SP points at the value at the top of the stack (most recently pushed), or at address F4 if the stack is empty.

# A function that takes in the current instruction and runs them in O(1) against our branchtable, 
# based on what the current instruction is.
    def handle_operations(self, IR, op_a, op_b, distance):
        if IR == LDI:
            self.branchtable[IR](op_a, op_b, distance)
        elif IR == PRN:
            self.branchtable[IR](op_a, distance)
        elif IR == MUL:
            self.branchtable[IR](op_a, op_b, distance)
        elif IR == PUSH:
            self.branchtable[IR](op_a, distance)
        elif IR == POP:
            self.branchtable[IR](op_a, distance)
        elif IR == CALL:
            self.branchtable[IR](op_a)
        elif IR == RET:
            self.branchtable[IR]()
        elif IR == ADD:
            self.branchtable[IR](op_a, op_b, distance)
        elif IR == HLT:
            self.branchtable[IR]()
        
    def handle_ADD(self, op_a, op_b, distance):
        self.alu('ADD', op_a, op_b)
        self.pc += distance
    
    def handle_CALL(self, op_a):
        # Get address of the instruction directly after CALL is pushed onto the stack. 
            #  This allows us to return to where we left off when the subroutine finishes executing.
        return_address = self.pc + 2

        # PUSH return address on stack
        self.stack_pointer -= 1
        self.ram[self.stack_pointer] = return_address
        # The PC is set to the address stored in the given register.
            # We jump to that location in RAM and execute the first instruction in the subroutine. 
            # The PC can move forward or backwards from its current location.
        #self.reg = self.ram[self.pc + 1]
        self.pc= self.reg[op_a] 
        #pass


    def handle_RET(self):
        self.pc = self.ram[self.stack_pointer]
        self.stack_pointer -= 1

    def handle_PUSH(self, op_a, distance):
        self.stack_pointer -=1  # decrement SP
        self.ram[self.stack_pointer] = self.reg[op_a]   # Copy the value in the given register to the address pointed to by SP
        self.pc += distance # move the pc
        #pass

    def handle_POP(self, op_a, distance):
        self.reg[op_a] = self.ram[self.stack_pointer]   # Copy the value from the address pointed to by SP to the given register.
        self.stack_pointer +=1 # Increment SP
        self.pc += distance # move the pc
        pass

    # A helper function that performs MUL per the ls8 spec.
    def handle_MUL(self, op_a, op_b, distance):
        self.alu('MUL', op_a, op_b)
        self.pc += distance

    # A helper function that performs HLT per the ls8 spec.
    def handle_HLT(self):
        running = False
        print("Halt. Drop. Roll.")
        return sys.exit(1)

    # A helper function that performs PRN per the ls8 spec.
    def handle_PRN(self, op_a, distance):
        print(self.reg[op_a])
        self.pc += distance

    # A helper function that performs LDI per the ls8 spec.
    def handle_LDI(self, op_a, op_b, distance):
        self.reg[op_a] = op_b
        self.pc += distance

    def ram_read(self, MAR):
        #MAR: Memory Address Register, holds the memory address we're reading or writing
        return self.ram[MAR]

    def ram_write(self, MAR, MDR):
        #MDR: Memory Data Register, holds the value to write or the value just read
        self.ram[MAR] = MDR

    def load(self):
        """Load a program into memory."""
        
        if len(sys.argv) != 2:
            print(f"usage: {sys.argv[0]} filename")
            sys.exit(1)

        try:
            with open(sys.argv[1]) as f:
                address = 0
                for line in f:
                    num = line.split("#", 1)[0]
                    if num.strip() == '':  # ignore comment-only lines
                        continue
                
                    #print(int(num))
                    self.ram[address] = int(num, 2)
                    address += 1
    
        except FileNotFoundError:
            print(f"{sys.argv[0]}: {sys.argv[1]} not found")
            sys.exit(2)


    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "MUL":
            self.reg[reg_a] = self.reg[reg_a] * self.reg[reg_b]
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            # self.fl,
            # self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        running = True
        
        while running:
            # Gets the current instruction from RAM
            IR = self.ram[self.pc]
            
            # Sets the first operand from ram (operand is a like a variable)
            op_a = self.ram_read(self.pc + 1)
            
            # sets the second operand from ram (operand is like a variable)
            op_b = self.ram_read(self.pc + 2)
            
            # gets the number of operands by using bitwise-AND to parse our instruction.
            num_operands = (IR & 0b11000000) >> 6
            
            # gets the number of operations that the pc will need to be incremented.
            dist_to_move_pc = num_operands + 1
            
            # A function that takes in the current instruction and runs them in O(1) against our branchtable, 
            # based on what the current instruction is.
            self.handle_operations(IR, op_a, op_b, dist_to_move_pc)