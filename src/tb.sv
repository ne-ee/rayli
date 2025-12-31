// tb.sv
module tb;
  timeunit 1ns;
  timeprecision 1ps;

  import "DPI-C" function int      py_init(input string ip, input int port);
  import "DPI-C" function int unsigned py_get(input int cycle);
  import "DPI-C" function void     py_close();

  logic clk = 0;
  always #5 clk = ~clk; // 100 MHz

  int cycle;
  int unsigned stim;

  initial begin
    cycle = 0;

    if (py_init("127.0.0.1", 50007) != 0) begin
      $fatal(1, "Failed to connect to Python server. Start py_server.py first.");
    end

    repeat (20) begin
      @(posedge clk);
      stim = py_get(cycle);
      $display("cycle=%0d stim=%0d (0x%08x)", cycle, stim, stim);
      cycle++;
    end

    py_close();
    $finish;
  end
endmodule
