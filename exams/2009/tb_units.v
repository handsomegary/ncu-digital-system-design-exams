`timescale 1ns/1ps

module tb_units;
    reg [1:0] vg, nb;
    reg select;
    wire [1:0] and_you, fine;
    CheerUp cheer(and_you, fine, vg, nb, select);

    reg ina, en;
    wire latched, tristate;
    EnabledLatch latch_unit(ina, en, latched);
    TriStateBuffer tri_unit(ina, en, tristate);

    reg [15:0] a, b, d;
    reg mux_select, lr, clk, rst;
    reg [1:0] ctr;
    wire [15:0] mux_out, shift_out, alu_out, q;
    MUX21 mux_unit(a, b, mux_select, mux_out);
    Shifter shift_unit(shift_out, a, lr);
    ALU alu_unit(alu_out, a, b, ctr);
    DFF16 dff_unit(q, d, clk, rst);

    reg dxclk, dxrst, s1, s2, s3, dlr;
    reg [1:0] mode;
    reg [15:0] din;
    wire [15:0] dout;
    MyDesign design_unit(s1, s2, s3, mode, dlr, din, dxclk, dxrst, dout);

    integer i, j, k, checked;
    reg [15:0] expected, model_x, model_y, old_output, next_x, next_y;
    reg [1:0] expected_fine;

    function [15:0] model_output;
        input [15:0] x, y, input_value;
        input select_x, left;
        input [1:0] operation;
        reg [15:0] operand, result;
        begin
            operand = select_x ? x : y;
            case (operation)
                0: result = operand + input_value;
                1: result = operand - input_value;
                2: result = operand + 16'd1;
                3: result = operand - 16'd1;
            endcase
            // Test oracle may use shifts; the synthesizable Shifter may not.
            model_output = left ? (result << 1) : (result >> 1);
        end
    endfunction

    initial begin
        checked = 0;
        vg = 0; nb = 0; select = 0;
        ina = 0; en = 0;
        a = 0; b = 0; d = 0; mux_select = 0; lr = 0; ctr = 0;
        clk = 0; rst = 0;
        dxclk = 0; dxrst = 0; s1 = 0; s2 = 0; s3 = 0;
        dlr = 0; mode = 0; din = 0;
        #1;
        if (latched !== 1'bx || tristate !== 1'bz || q !== 16'h0000)
            $fatal(1, "initial latch/tristate/reset mismatch");
        en = 1; ina = 1; #1;
        if (latched !== 1 || tristate !== 1) $fatal(1, "enabled buffer mismatch");
        en = 0; ina = 0; #1;
        if (latched !== 1 || tristate !== 1'bz) $fatal(1, "hold/Z mismatch");
        en = 1; #1;
        if (latched !== 0 || tristate !== 0) $fatal(1, "transparent latch mismatch");
        checked = checked + 4;

        for (i = 0; i < 4; i = i + 1)
            for (j = 0; j < 4; j = j + 1)
                for (k = 0; k < 2; k = k + 1) begin
                    vg = i; nb = j; select = k;
                    expected_fine[0] = (i >> (k ? 0 : 1)) & 1;
                    expected_fine[1] = (j >> (k ? 0 : 1)) & 1;
                    #1;
                    if (and_you !== (vg | nb) || fine !== expected_fine)
                        $fatal(1, "CheerUp mismatch");
                    checked = checked + 1;
                end

        for (i = 0; i < 65536; i = i + 1) begin
            a = i;
            lr = 0; #1;
            expected = i / 2;
            if (shift_out !== expected) $fatal(1, "right shift mismatch %0d", i);
            lr = 1; #1;
            expected = (i * 2) % 65536;
            if (shift_out !== expected) $fatal(1, "left shift mismatch %0d", i);
            checked = checked + 2;
        end

        for (i = 0; i < 1024; i = i + 1) begin
            a = (i * 61) & 65535;
            b = ~a;
            mux_select = 0; #1;
            if (mux_out !== b) $fatal(1, "MUX inb mismatch");
            mux_select = 1; #1;
            if (mux_out !== a) $fatal(1, "MUX ina mismatch");
            checked = checked + 2;
            for (j = 0; j < 4; j = j + 1) begin
                case (j)
                    0: b = 0;
                    1: b = 1;
                    2: b = 16'hffff;
                    3: b = a ^ 16'ha5a5;
                endcase
                for (k = 0; k < 4; k = k + 1) begin
                    ctr = k;
                    case (k)
                        0: expected = a + b;
                        1: expected = a - b;
                        2: expected = a + 16'd1;
                        3: expected = a - 16'd1;
                    endcase
                    #1;
                    if (alu_out !== expected) $fatal(1, "ALU mismatch");
                    checked = checked + 1;
                end
            end
        end

        rst = 1; d = 16'h1234; #1;
        if (q !== 0) $fatal(1, "DFF changed without edge");
        clk = 1; #1;
        if (q !== 16'h1234) $fatal(1, "DFF did not capture on positive edge");
        d = 16'habcd; #1;
        if (q !== 16'h1234) $fatal(1, "DFF transparent while clock high");
        rst = 0; #1;
        if (q !== 0) $fatal(1, "asynchronous reset did not clear immediately");
        rst = 1; clk = 0; #1; clk = 1; #1;
        if (q !== 16'habcd) $fatal(1, "DFF release/capture mismatch");
        checked = checked + 5;

        model_x = 0; model_y = 0;
        dxrst = 1;
        for (i = 0; i < 2048; i = i + 1) begin
            dxclk = 0;
            s1 = i & 1; s2 = (i >> 1) & 1; s3 = (i >> 2) & 1;
            mode = (i >> 3) & 3; dlr = (i >> 5) & 1;
            din = (i * 7919) ^ 16'ha5a5;
            #1;
            old_output = model_output(model_x, model_y, din, s3, dlr, mode);
            if (dout !== old_output) $fatal(1, "datapath before edge mismatch");
            next_x = s1 ? model_x : old_output;
            next_y = s2 ? model_y : old_output;
            dxclk = 1; #1;
            model_x = next_x; model_y = next_y;
            expected = model_output(model_x, model_y, din, s3, dlr, mode);
            if (design_unit.x !== model_x || design_unit.y !== model_y || dout !== expected)
                $fatal(1, "datapath after edge mismatch");
            checked = checked + 2;
        end
        $display("PASS units checks=%0d", checked);
        $finish(0);
    end
endmodule
