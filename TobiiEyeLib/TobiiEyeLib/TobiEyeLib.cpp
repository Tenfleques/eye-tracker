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


bool updating = false;
IL::UniqueInteractionLibPtr intlib(IL::CreateInteractionLib(IL::FieldOfUse::Interactive));

// assume single screen with size 2560x1440 and use full screen (not window local) coordinates
constexpr float width = 2560.0f;
constexpr float height = 1440.0f;
constexpr float offset = 0.0f;


struct Record {
    Record() {
        this->x = 0.0;
        this->y = 0.0;
    }
    Record(IL::GazePointData evt) {
        this->x = evt.x;
        this->y = evt.y;
        this->timestamp = double(evt.timestamp_us);
        this->engineTimestamp = double(evt.timestamp_us);
        this->valid = evt.validity == IL::Validity::Valid;
    };

    double x, y, timestamp, engineTimestamp;
    bool valid = false;
};
std::deque<Record> latestRecords = std::deque<Record>(10);

int stop() {
    
    if (updating) {
        updating = false;
        update_thread.join();
        return 1;
    }    
    return 0;
}

void updateRecords() {
    intlib->CoordinateTransformAddOrUpdateDisplayArea(width, height);
    intlib->CoordinateTransformSetOriginOffset(offset, offset);
    intlib->SubscribeGazePointData([](IL::GazePointData evt, void* context) {
        double res[size] = { evt.x, evt.y, double(evt.validity == IL::Validity::Valid), double(evt.timestamp_us) };
        //
        std::stringstream ss;
        ss << evt.x << ","
            << evt.y << ","
            << double(evt.validity == IL::Validity::Valid) << ","
            << double(evt.timestamp_us);

        std::string s = ss.str();

        //std::cout
        //    << s
        //    << "\n";
        latestRecords.push_front(Record(evt));
    }, nullptr);

    while (updating) {
        intlib->WaitAndUpdate();
    }
}

int start() {
    for (int i = 0; i < 10; ++i) {
        latestRecords.push_front(Record());
    }
    if (!updating) {
        updating = true;
        update_thread = std::thread(updateRecords);
    }
    return update_thread.joinable();
}

Record* getLatest() {
    Record* r = new Record[10];
    for (int i = 0; i < 10; ++i) {
        r[i] = latestRecords[i];
    }
    return r;
}