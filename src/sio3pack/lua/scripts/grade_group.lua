--[[
The template bellow contains a mapping of the test ID to the register name.
Example:
{
    ["0"] = "grade_res_0",
    ["1a"] = "grade_res_1a",
    ["1b"] = "grade_res_1b",
}

]]--
local test_grading = <LUA_MAP_TEST_ID_REG>

for reg, test_id in pairs(outgens) do
    -- do some epic grading stuff
    print("ok")
end
