#pragma once

#ifdef TOBIEYELIB_EXPORTS
#define TOBIEYELIB_API __declspec(dllexport)
#else
#define TOBIEYELIB_API __declspec(dllimport)
#endif

struct Record;

extern "C" TOBIEYELIB_API int stop();

//extern "C" TOBIEYELIB_API int start(int cam_index =  0);

extern "C" TOBIEYELIB_API int start(int cam_index, char* images_path);

//extern "C" TOBIEYELIB_API Record* get_latest();

extern "C" TOBIEYELIB_API Record * get_latest(int frame_id);

extern "C" TOBIEYELIB_API Record * get_records(int frame_id);