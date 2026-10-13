`timescale 1ns/1ps
`default_nettype none
module tb_2023;
    reg Clk;
    integer handle, status, index, j, bit_number, which;
    integer a, b, c, mode, v0, v1, v2, v3, v4, v5, v6, v7, v8;
    integer enable_value, reset_value, write_address, data_value, ra, rb, rc;
    reg [7:0] rotate_a, rotate_b, rotate_c;
    reg [1:0] rotate_mode;
    wire [7:0] rotate_o1, rotate_o2, rotate_o3;
    Rotator rotate(rotate_o3, rotate_o2, rotate_o1, rotate_c, rotate_b, rotate_a, rotate_mode);

    reg [7:0] row_a, row_b, row_c;
    reg row_mode;
    wire [7:0] row_value;
    wire [1:0] row_position;
    wire row_valid;
    RowComparator row(row_value, row_position, row_valid, row_a, row_b, row_c, row_mode);

    reg [71:0] pattern_data;
    reg [1:0] pattern_mode;
    wire [7:0] pattern_value;
    wire [1:0] pattern_row, pattern_column;
    wire pattern_valid;
    PatternComparator3x3 pattern(pattern_value, pattern_row, pattern_column, pattern_valid,
        pattern_data[7:0], pattern_data[15:8], pattern_data[23:16],
        pattern_data[31:24], pattern_data[39:32], pattern_data[47:40],
        pattern_data[55:48], pattern_data[63:56], pattern_data[71:64], pattern_mode);

    reg rf_we;
    reg [7:0] rf_data;
    reg [9:0] rf_wa, rf_ra, rf_rb, rf_rc;
    wire [7:0] rf_qa, rf_qb, rf_qc;
    RegisterFile rf(rf_qa, rf_qb, rf_qc, rf_data, Clk, rf_ra, rf_rb, rf_rc, rf_we, rf_wa);

    reg count_reset, count_enable;
    wire [6:0] count_x;
    wire [5:0] count_y;
    Count2D #(.COL(4), .ROW(7)) counter(count_x, count_y, Clk, count_reset, count_enable);

    reg fetch_reset, fetch_enable;
    reg [6:0] fetch_x;
    reg [5:0] fetch_y;
    wire fetch_valid, default_valid;
    wire [7:0] fetch_top, fetch_middle, fetch_bottom, default_top, default_middle, default_bottom;
    DataFetch #(.COL(4), .ROW(7)) fetch(fetch_valid, fetch_top, fetch_middle, fetch_bottom, fetch_x, fetch_y, fetch_enable, Clk, fetch_reset);
    DataFetch default_fetch(default_valid, default_top, default_middle, default_bottom, fetch_x, fetch_y, fetch_enable, Clk, fetch_reset);

    reg max_reset, max_enable;
    reg [1:0] max_pattern;
    wire [7:0] max_value;
    wire [6:0] max_x;
    wire [5:0] max_y;
    wire max_valid;
    MaxSearch2D #(.COL(4), .ROW(7)) maximum(max_value, max_x, max_y, max_valid, Clk, max_reset, max_enable, max_pattern);

    task tick;
        begin #5; Clk = 1; #1; end
    endtask
    task tock;
        begin #4; Clk = 0; #1; end
    endtask

    initial begin
        Clk = 0;
        rotate_a = 0; rotate_b = 0; rotate_c = 0; rotate_mode = 0;
        row_a = 0; row_b = 0; row_c = 0; row_mode = 0;
        pattern_data = 0; pattern_mode = 0;
        rf_we = 0; rf_data = 0; rf_wa = 0; rf_ra = 0; rf_rb = 0; rf_rc = 0;
        count_reset = 1; count_enable = 0;
        fetch_reset = 1; fetch_enable = 0; fetch_x = 0; fetch_y = 0;
        max_reset = 1; max_enable = 0; max_pattern = 2;
        $readmemh("memory.hex", rf.MemArray);
        $readmemh("memory.hex", fetch.U6_1.MemArray);
        $readmemh("memory.hex", default_fetch.U6_1.MemArray);
        $readmemh("memory.hex", maximum.U7_2.U6_1.MemArray);
        #1;

        handle = $fopen("rotator_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing rotator vectors");
        index = 0;
        status = $fscanf(handle, "%d %d %d %d\n", mode, a, b, c);
        while (status == 4) begin
            rotate_mode = mode; rotate_a = a; rotate_b = b; rotate_c = c;
            #1;
            $display("ROT %0d %0d %0d %0d", index, rotate_o1, rotate_o2, rotate_o3);
            index = index + 1;
            status = $fscanf(handle, "%d %d %d %d\n", mode, a, b, c);
        end
        $fclose(handle);
        rotate_mode = 2'bx1; #1;
        $display("ROT_UNKNOWN %0d %0d %0d", rotate_o1, rotate_o2, rotate_o3);

        handle = $fopen("row_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing row vectors");
        index = 0;
        status = $fscanf(handle, "%d %d %d %d\n", mode, a, b, c);
        while (status == 4) begin
            row_mode = mode; row_a = a; row_b = b; row_c = c; #1;
            $display("ROW %0d %0d %0d %0d", index, row_value, row_position, row_valid);
            index = index + 1;
            status = $fscanf(handle, "%d %d %d %d\n", mode, a, b, c);
        end
        $fclose(handle);
        index = 0;
        for (mode = 0; mode < 2; mode = mode + 1)
            for (which = 0; which < 3; which = which + 1)
                for (bit_number = 0; bit_number < 8; bit_number = bit_number + 1)
                    for (j = 0; j < 2; j = j + 1) begin
                        row_mode = mode; row_a = 93; row_b = 57; row_c = 11;
                        if (which == 0) row_a[bit_number] = j ? 1'bz : 1'bx;
                        if (which == 1) row_b[bit_number] = j ? 1'bz : 1'bx;
                        if (which == 2) row_c[bit_number] = j ? 1'bz : 1'bx;
                        #1; $display("ROW_UNKNOWN %0d %0d %0d %0d", index, row_value, row_position, row_valid);
                        index = index + 1;
                    end
        row_a = 1; row_b = 2; row_c = 3; row_mode = 1'bx; #1;
        $display("ROW_UNKNOWN %0d %0d %0d %0d", index, row_value, row_position, row_valid);

        handle = $fopen("pattern_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing pattern vectors");
        index = 0;
        status = $fscanf(handle, "%d %d %d %d %d %d %d %d %d %d\n", mode, v0, v1, v2, v3, v4, v5, v6, v7, v8);
        while (status == 10) begin
            pattern_mode = mode;
            pattern_data = {v8[7:0], v7[7:0], v6[7:0], v5[7:0], v4[7:0], v3[7:0], v2[7:0], v1[7:0], v0[7:0]};
            #1; $display("PAT %0d %0d %0d %0d %0d", index, pattern_value, pattern_row, pattern_column, pattern_valid);
            index = index + 1;
            status = $fscanf(handle, "%d %d %d %d %d %d %d %d %d %d\n", mode, v0, v1, v2, v3, v4, v5, v6, v7, v8);
        end
        $fclose(handle);
        index = 0;
        for (mode = 0; mode < 3; mode = mode + 1)
            for (which = 0; which < 9; which = which + 1)
                for (j = 0; j < 2; j = j + 1) begin
                    pattern_mode = mode; pattern_data = {9{8'd57}};
                    pattern_data[8 * which + 3] = j ? 1'bz : 1'bx;
                    #1; $display("PAT_UNKNOWN %0d %0d %0d %0d %0d", index, pattern_value, pattern_row, pattern_column, pattern_valid);
                    index = index + 1;
                end
        pattern_mode = 2'bx0; pattern_data = {9{8'd1}}; #1;
        $display("PAT_UNKNOWN %0d %0d %0d %0d %0d", index, pattern_value, pattern_row, pattern_column, pattern_valid);

        handle = $fopen("rf_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing register file vectors");
        index = 0;
        status = $fscanf(handle, "%d %d %d %d %d %d\n", enable_value, write_address, data_value, ra, rb, rc);
        while (status == 6) begin
            rf_we = enable_value; rf_wa = write_address; rf_data = data_value;
            rf_ra = ra; rf_rb = rb; rf_rc = rc;
            tick; $display("RF %0d %0d %0d %0d", index, rf_qa, rf_qb, rf_qc); tock;
            index = index + 1;
            status = $fscanf(handle, "%d %d %d %d %d %d\n", enable_value, write_address, data_value, ra, rb, rc);
        end
        $fclose(handle); rf_we = 0;
        v0 = rf_qa; rf_ra = rf_ra + 1; #1;
        $display("RF_HOLD %0d %0d", v0, rf_qa);

        count_reset = 0; count_enable = 1; tick; tock; tick; tock;
        count_reset = 1; #1;
        $display("COUNT_ASYNC %0d %0d", count_x, count_y);
        count_reset = 0;
        handle = $fopen("count_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing counter vectors");
        index = 0;
        status = $fscanf(handle, "%d %d\n", reset_value, enable_value);
        while (status == 2) begin
            count_reset = reset_value; count_enable = enable_value;
            tick; $display("COUNT %0d %0d %0d", index, count_x, count_y); tock;
            index = index + 1;
            status = $fscanf(handle, "%d %d\n", reset_value, enable_value);
        end
        $fclose(handle); count_enable = 0;

        fetch_reset = 0;
        handle = $fopen("fetch_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing fetch vectors");
        index = 0;
        status = $fscanf(handle, "%d %d %d\n", ra, rb, enable_value);
        while (status == 3) begin
            fetch_x = ra; fetch_y = rb; fetch_enable = enable_value;
            tick;
            $display("FETCH %0d %0d %h %h %h", index, fetch_valid, fetch_top, fetch_middle, fetch_bottom);
            $display("DEFAULT_FETCH %0d %0d %h %h %h", index, default_valid, default_top, default_middle, default_bottom);
            tock; index = index + 1;
            status = $fscanf(handle, "%d %d %d\n", ra, rb, enable_value);
        end
        $fclose(handle);
        fetch_x = 7'hxx; fetch_y = 1; fetch_enable = 1;
        tick; $display("FETCH_UNKNOWN %0d", fetch_valid); tock;
        fetch_reset = 1; #1; $display("FETCH_ASYNC %0d", fetch_valid);
        fetch_enable = 0;

        handle = $fopen("max_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing maximum search vectors");
        index = 0;
        status = $fscanf(handle, "%d %d %d\n", reset_value, enable_value, mode);
        while (status == 3) begin
            max_reset = reset_value; max_enable = enable_value; max_pattern = mode;
            tick; $display("MAX %0d %0d %0d %0d %0d", index, max_value, max_x, max_y, max_valid); tock;
            index = index + 1;
            status = $fscanf(handle, "%d %d %d\n", reset_value, enable_value, mode);
        end
        $fclose(handle);
        max_reset = 1; #1; $display("MAX_ASYNC %0d %0d %0d %0d", max_value, max_x, max_y, max_valid);
        maximum.U7_2.U6_1.MemArray[0] = 8'b000x0000;
        max_reset = 0; max_enable = 1; max_pattern = 2;
        for (j = 0; j < 4; j = j + 1) begin tick; tock; end
        $display("MAX_UNKNOWN %0d %0d %0d %0d", max_value, max_x, max_y, max_valid);
        $display("DONE");
        $finish(0);
    end
endmodule
`default_nettype wire
