#pragma once

#ifdef TOBIEYELIB_EXPORTS
#define TOBIEYELIB_API __declspec(dllexport)
#else
#define TOBIEYELIB_API __declspec(dllimport)
#endif


struct SessionRecord;


extern "C" TOBIEYELIB_API long save_images(const char* out_path = nullptr);

extern "C" TOBIEYELIB_API int run(const char* src_path = nullptr,
    const char* out_path = nullptr);

extern "C" TOBIEYELIB_API const char* get_json();

extern "C" TOBIEYELIB_API SessionRecord* get_session();