`timescale 1ns/1ps

module tb_2008;
    reg A1, B1, x1, y1;
    reg A2, B2, x2;
    wire DA1, DB1, z1, DA2, DB2, z2;
    reg clk, reset, sx, sy;
    wire QA1, QB1, sz1, QA2, QB2, sz2;
    reg [1:0] reference1, reference2, future1, future2;
    integer i, checks;

    q1_next c1(A1, B1, x1, y1, DA1, DB1, z1);
    q2_next c2(A2, B2, x2, DA2, DB2, z2);
    q1_seq s1(clk, reset, sx, sy, QA1, QB1, sz1);
    q2_seq s2(clk, reset, sx, QA2, QB2, sz2);

    // Independent reference: complete state table, not the DUT gate expression.
    function [1:0] expected1;
        input [3:0] key;
        begin
            case (key)
                0, 1, 2, 6, 10, 14: expected1 = 2'b00;
                3, 4, 5, 7, 11, 15: expected1 = 2'b10;
                8, 9: expected1 = 2'b01;
                12, 13: expected1 = 2'b11;
                default: expected1 = 2'bxx;
            endcase
        end
    endfunction

    // Independent reference: original state-diagram destination labels.
    function [1:0] expected2;
        input [2:0] key;
        begin
            case (key)
                0: expected2 = 2'b10;
                1: expected2 = 2'b00;
                2: expected2 = 2'b11;
                3: expected2 = 2'b01;
                4: expected2 = 2'b01;
                5: expected2 = 2'b11;
                6: expected2 = 2'b00;
                7: expected2 = 2'b10;
                default: expected2 = 2'bxx;
            endcase
        end
    endfunction

    initial begin
        checks = 0;
        clk = 0; reset = 0; sx = 0; sy = 0;
        A1 = 0; B1 = 0; x1 = 0; y1 = 0;
        A2 = 0; B2 = 0; x2 = 0;
        for (i = 0; i < 16; i = i + 1) begin
            {A1, B1, x1, y1} = i[3:0];
            #1;
            if ({DA1, DB1} !== expected1(i[3:0]))
                $fatal(1, "Q1 next-state mismatch, key=%0d", i);
            if (z1 !== (i >= 12))
                $fatal(1, "Q1 present-state output mismatch, key=%0d", i);
            checks = checks + 1;
        end
        for (i = 0; i < 8; i = i + 1) begin
            {A2, B2, x2} = i[2:0];
            #1;
            if ({DA2, DB2} !== expected2(i[2:0]))
                $fatal(1, "Q2 next-state mismatch, key=%0d", i);
            if (z2 !== ((i == 2) || (i == 3)))
                $fatal(1, "Q2 graph output mismatch, key=%0d", i);
            checks = checks + 1;
        end
        // State 11 is valid in the original uninitialized circuit, even though
        // reset-to-00 operation cannot reach it. Sample its present-state output.
        force s1.A = 1'b1;
        force s1.B = 1'b1;
        sx = 1; sy = 0;
        #1;
        if (sz1 !== 1'b1) $fatal(1, "Q1 state 11 output uses the wrong time index");
        release s1.A;
        release s1.B;
        checks = checks + 1;
        // Reset occurs away from a rising clock edge.
        reset = 1;
        #1;
        if ({QA1, QB1, QA2, QB2} !== 4'b0000)
            $fatal(1, "Asynchronous reset did not clear both states");
        checks = checks + 1;
        reset = 0;
        reference1 = 0; reference2 = 0;
        for (i = 0; i < 64; i = i + 1) begin
            // This short repeating path traverses all eight Q2 graph edges.
            case (i % 12)
                3, 4, 6, 9: sx = 1;
                default: sx = 0;
            endcase
            sy = i[1] ^ i[3];
            future1 = expected1({reference1, sx, sy});
            future2 = expected2({reference2, sx});
            #2; clk = 1; #1;
            reference1 = future1;
            reference2 = future2;
            if ({QA1, QB1} !== reference1 || {QA2, QB2} !== reference2)
                $fatal(1, "Sequential next-state mismatch, cycle=%0d", i);
            if (sz1 !== (reference1 == 2'b11) || sz2 !== (reference2 == 2'b01))
                $fatal(1, "Sequential Moore output mismatch, cycle=%0d", i);
            checks = checks + 1;
            #2; clk = 0;
        end
        #1; reset = 1; #1;
        if ({QA1, QB1, QA2, QB2} !== 4'b0000 || sz1 !== 1'b0 || sz2 !== 1'b0)
            $fatal(1, "Reset after active operation failed");
        checks = checks + 1;
        $display("PASS 2008: %0d checks", checks);
        $finish(0);
    end
endmodule
