#include "pch.h" // use stdafx.h in Visual Studio 2017 and earlier
#include <tobii/tobii.h>
#include <tobii/tobii_streams.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include <limits.h>
#include <deque>
#include <thread>
#include <chrono>
#include "TobiEyeLib.h"
#include <windows.h>

double timeInMilliseconds() {
    SYSTEMTIME tim;
    GetSystemTime(&tim);
    double time_ms = time(0) + tim.wMilliseconds/1000.0;
    return time_ms;
}

struct Point2D {
    Point2D(const float x, const float y) : x(x), y(y) {};
    Point2D(const float l[2]) : x(l[0]), y(l[1]) {};
    Point2D() : x(.0), y(.0) {};
    void setX(const float xx) {
        x = xx;
    }
    void setY(const float yy) {
        y = yy;
    }
    void print() {
        printf("x %f, y %f \n", x, y);
    }
    float x = .0, y = .0;
};
struct Point3D : Point2D {
    Point3D(const float x, const float y, const float zz) {
        z = zz;
        this->setX(x);
        this->setY(y);
    };
    Point3D(const float l[3]) {
        this->setX(l[0]);
        this->setY(l[1]);
        z = l[2];
    };
    Point3D() {
        z = .0;
    };
    void setZ(const float zz) {
        z = zz;
    }
    void print() {
        printf("x %f, y %f, z %f \n", x, y, z);
    }
    float z;
};
struct Eye {
    Eye(Point3D l, Point3D r) : left(l), right(r) {};
    Eye(const float l[3], const float r[3]) : left(Point3D(l)), right(Point3D(r)) {};
    Eye() : left(Point3D()), right(Point3D()) {};

    void setLeft(Point3D l) {
        left = l;
    }
    void setRight(Point3D r) {
        right = r;
    }
    void print() {
        left.print();
        right.print();
    }
    Point3D left, right;
};

struct Record {
    Record() : gaze(Point2D()),
        origin(Eye()), pos(Eye()),
        gaze_timestamp_us(0), origin_timestamp_us(0), pos_timestamp_us(0),
        sys_clock(timeInMilliseconds()),
        gaze_valid(false), pos_valid(false), origin_valid(false)
    {};

    Record(tobii_gaze_point_t const* gaze_point,
        tobii_gaze_origin_t const* gaze_origin,
        tobii_eye_position_normalized_t const* eye_pos) :

        gaze(Point2D(gaze_point->position_xy)),
        origin(Eye(gaze_origin->left_xyz, gaze_origin->right_xyz)),
        pos(Eye(eye_pos->left_xyz, eye_pos->right_xyz)),
        gaze_timestamp_us(gaze_point->timestamp_us),
        origin_timestamp_us(gaze_origin->timestamp_us),
        pos_timestamp_us(eye_pos->timestamp_us),
        sys_clock(timeInMilliseconds()),
        gaze_valid(gaze_point->validity == TOBII_VALIDITY_VALID),
        pos_valid(eye_pos->left_validity == TOBII_VALIDITY_VALID
            && eye_pos->right_validity == TOBII_VALIDITY_VALID),
        origin_valid(gaze_origin->left_validity == TOBII_VALIDITY_VALID
            && gaze_origin->right_validity == TOBII_VALIDITY_VALID)
    {};


    void setGaze(tobii_gaze_point_t const* gaze_point) {
        gaze = Point2D(gaze_point->position_xy);
        gaze_valid = gaze_point->validity == TOBII_VALIDITY_VALID;
        gaze_timestamp_us = gaze_point->timestamp_us;
        sys_clock = timeInMilliseconds();
    }
    void setOrigin(tobii_gaze_origin_t const* gaze_origin) {
        origin = Eye(gaze_origin->left_xyz, gaze_origin->right_xyz);
        origin_valid = gaze_origin->left_validity == TOBII_VALIDITY_VALID
            && gaze_origin->right_validity == TOBII_VALIDITY_VALID;
        origin_timestamp_us = gaze_origin->timestamp_us;
        sys_clock = timeInMilliseconds();
    }
    void setPos(tobii_eye_position_normalized_t const* eye_pos) {
        pos = Eye(eye_pos->left_xyz, eye_pos->right_xyz);
        pos_valid = eye_pos->left_validity == TOBII_VALIDITY_VALID
            && eye_pos->right_validity == TOBII_VALIDITY_VALID;
        pos_timestamp_us = eye_pos->timestamp_us;
        sys_clock = timeInMilliseconds();
    }
    void print() {
        gaze.print();
        origin.print();
        pos.print();
        printf("time %Ii %Ii %Ii \n\n", gaze_timestamp_us, origin_timestamp_us, pos_timestamp_us);
    }
    Point2D gaze;
    Eye origin, pos;
    int64_t gaze_timestamp_us = 0,
        origin_timestamp_us = 0,
        pos_timestamp_us = 0;
    double sys_clock = timeInMilliseconds();
    bool gaze_valid = false, pos_valid = false, origin_valid = false;
};

// the temporary record to update in the callbacks 
Record tmp_record;
std::deque<Record> latestRecords = std::deque<Record>(10);
// the queue with the top 10 recent records 


void gaze_point_callback(tobii_gaze_point_t const* gaze_point, void* /* user_data */) {
    tmp_record.setGaze(gaze_point);
}

void gaze_origin_callback(tobii_gaze_origin_t const* gaze_origin, void* user_data) {
    tmp_record.setOrigin(gaze_origin);
}
void eye_position_callback(tobii_eye_position_normalized_t const* eye_pos, void* user_data) {
    tmp_record.setPos(eye_pos);
}

void url_receiver(char const* url, void* user_data){
    char* buffer = (char*)user_data;
    if (*buffer != '\0') return; // only keep first value

    if (strlen(url) < 256)
        strcpy(buffer, url);
}

std::thread update_thread;
bool updating = false;
// Create API
tobii_api_t* api = NULL;
// Connect to the first tracker found
tobii_device_t* device = NULL;
// status flag 
tobii_error_t result = tobii_api_create(&api, NULL, NULL);


void updateRecords() {
    while (updating) {
        // Optionally block this thread until data is available. Especially useful if running in a separate thread.
        result = tobii_wait_for_callbacks(1, &device);
        assert(result == TOBII_ERROR_NO_ERROR || result == TOBII_ERROR_TIMED_OUT);

        // Process callbacks on this thread if data is available
        result = tobii_device_process_callbacks(device);
        assert(result == TOBII_ERROR_NO_ERROR);

        //latestRecords.push_front(Record(tmp_record));
    }
}

int start() {
    if (result != TOBII_ERROR_NO_ERROR) 
        printf("%s\n", tobii_error_message(result));

    assert(result == TOBII_ERROR_NO_ERROR);

    // Enumerate devices to find connected eye trackers, keep the first
    char url[256] = { 0 };
    result = tobii_enumerate_local_device_urls(api, url_receiver, url);
    

    if (result != TOBII_ERROR_NO_ERROR)
        printf("%s\n", tobii_error_message(result));
    assert(result == TOBII_ERROR_NO_ERROR);

    if (*url == '\0'){
        printf("Error: No device found\n");
        return 0;
    }

    result = tobii_device_create(api, url, TOBII_FIELD_OF_USE_INTERACTIVE, &device);

    if (result != TOBII_ERROR_NO_ERROR)
        printf("%s\n", tobii_error_message(result));
    assert(result == TOBII_ERROR_NO_ERROR);

    // Subscribe to gaze data
    result = tobii_gaze_point_subscribe(device, gaze_point_callback, 0);
    result = tobii_gaze_origin_subscribe(device, gaze_origin_callback, 0);
    result = tobii_eye_position_normalized_subscribe(device, eye_position_callback, 0);

    if (result != TOBII_ERROR_NO_ERROR)
        printf("%s\n", tobii_error_message(result));
    assert(result == TOBII_ERROR_NO_ERROR);

    for (int i = 0; i < 10; ++i) {
        latestRecords.push_front(Record());
    }
    if (!updating) {
        updating = true;
        update_thread = std::thread(updateRecords);
    }
    return update_thread.joinable();
}


int stop() {
    if (updating) {
        updating = false;
        update_thread.join();
    }

    // Cleanup
    if (device != NULL) {
        result = tobii_gaze_point_unsubscribe(device);
        if (result != TOBII_ERROR_NO_ERROR)
            printf("%s\n", tobii_error_message(result));
        assert(result == TOBII_ERROR_NO_ERROR);

        result = tobii_device_destroy(device);
        if (result != TOBII_ERROR_NO_ERROR)
            printf("%s\n", tobii_error_message(result));
        assert(result == TOBII_ERROR_NO_ERROR);
    }
    if (api != NULL) {
        result = tobii_api_destroy(api);
        if (result != TOBII_ERROR_NO_ERROR)
            printf("%s\n", tobii_error_message(result));
        assert(result == TOBII_ERROR_NO_ERROR);
    }

    return 0;
}


Record* getLatest() {
    return &tmp_record;
}