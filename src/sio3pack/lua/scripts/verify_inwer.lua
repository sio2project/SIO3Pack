--[[
The template bellow contains a mapping of the test ID to the register name.
Example:
{
    ["0"] = "outgen_res_0",
    ["1a"] = "outgen_res_1a",
    ["1b"] = "outgen_res_1b",
}

]]--
local outgens = <LUA_MAP_TEST_ID_REG>

for reg, test_id in pairs(outgens) do
    -- do some epic inwer stuff
    print("ok")
end
