#include <emscripten/emscripten.h>
#include <emscripten/bind.h>
#include "aldehyde.cpp"

using namespace emscripten;

// Export the parser function to JavaScript
EMSCRIPTEN_BINDINGS(aldehyde_module) {
    function("parseToString", &Aldehyde::AldehydeParserToString);
}

// C-style export for direct calling
extern "C" {
    EMSCRIPTEN_KEEPALIVE
    const char* parse_molecule(const char* name) {
        static std::string result;
        result = Aldehyde::AldehydeParserToString(std::string(name));
        return result.c_str();
    }
}