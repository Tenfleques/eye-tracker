#pragma once

#ifdef TOBIEYELIB_EXPORTS
#define TOBIEYELIB_API __declspec(dllexport)
#else
#define TOBIEYELIB_API __declspec(dllimport)
#endif

struct Record;

extern "C" TOBIEYELIB_API int stop();

extern "C" TOBIEYELIB_API int start();

extern "C" TOBIEYELIB_API Record* getLatest();