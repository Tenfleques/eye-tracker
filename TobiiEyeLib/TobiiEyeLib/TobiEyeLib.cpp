#include "pch.h" // use stdafx.h in Visual Studio 2017 and earlier
#include <utility>
#include <limits.h>
#include <deque>
#include <iostream>
#include <sstream>
#include <thread>  
#include <interaction_lib/InteractionLib.h>
#include <interaction_lib/misc/InteractionLibPtr.h>
#include "TobiEyeLib.h"

const int size = 4;
std::thread update_thread;

//double def[size] = {.0, .0, .0, .0};

std::deque<const char*> latestRecords = std::deque<const char*>(10);

bool updating = false;
IL::UniqueInteractionLibPtr intlib(IL::CreateInteractionLib(IL::FieldOfUse::Interactive));

// assume single screen with size 2560x1440 and use full screen (not window local) coordinates
constexpr float width = 2560.0f;
constexpr float height = 1440.0f;
constexpr float offset = 0.0f;



int stop() {
    if (updating) {
        updating = false;
        update_thread.join();
        //update_thread.detach();
        return 1;
    }    
	return 0;
}

void updateRecords() {
    intlib->CoordinateTransformAddOrUpdateDisplayArea(width, height);
    intlib->CoordinateTransformSetOriginOffset(offset, offset);
    intlib->SubscribeGazePointData([](IL::GazePointData evt, void* context) {
        double res[size] = { evt.x, evt.y, double(evt.validity == IL::Validity::Valid), double(evt.timestamp_us) };
        //latestRecords.push_front(res);
        std::stringstream ss;
        ss << evt.x << ","
            << evt.y << ","
            << double(evt.validity == IL::Validity::Valid) << ","
            << double(evt.timestamp_us);

        std::string s = ss.str();

        //std::cout
        //    << s
        //    << "\n";

        const char* c_s = s.c_str();


    }, nullptr);

    while (updating) {
        intlib->WaitAndUpdate();
    }
}

int start() {
    for (int i = 0; i < 10; ++i) {
        const char* init_res = std::string("0,0,0,0").c_str();
        latestRecords.push_front(init_res);
    }
    if (!updating) {
        updating = true;
        update_thread = std::thread(updateRecords);
    }
    return update_thread.joinable();
}

double** getLatest() {
    double** r = new double*[10];
    for (int i = 0; i < 10; ++i) {
        r[i] = new double[size];
        for (int j = 0; j < size; ++j) {
            r[i][j] = latestRecords[i][j];
        }
    }
    return r;
}