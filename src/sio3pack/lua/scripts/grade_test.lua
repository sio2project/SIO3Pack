--[[

This script checks and grades a user's solution on a test. It gets two registers,
checker status and solution status, as well as an object, which is the checkers output.

]]--

local solution_status = get_register(0)
local checker_status = get_register(1)
local checker_out_obj = get_object(0)
local checker_out = checker_out_obj:get_value()

print("checker_out: " .. checker_out)
