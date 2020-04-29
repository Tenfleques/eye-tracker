#include <tobii/tobii.h>
#include <tobii/tobii_streams.h>
#include <stdio.h>
#include <assert.h>
#include <limits.h>
#include <thread>
#include <chrono>
#include "TobiEyeLib.h"
#include <windows.h>
#include "opencv2/opencv.hpp"
#include <string>
#include <deque>

using namespace cv;

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
    }
    void setPos(tobii_eye_position_normalized_t const* eye_pos) {
        pos = Eye(eye_pos->left_xyz, eye_pos->right_xyz);
        pos_valid = eye_pos->left_validity == TOBII_VALIDITY_VALID
            && eye_pos->right_validity == TOBII_VALIDITY_VALID;
        pos_timestamp_us = eye_pos->timestamp_us;
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
    double sys_clock = timeInMilliseconds(), selfie_time = timeInMilliseconds();
    bool gaze_valid = false, pos_valid = false, origin_valid = false;
    
    Point3D img_shape;
};

std::thread update_thread;
bool updating = false;
// Create API
tobii_api_t* api = NULL;
// Connect to the first tracker found
tobii_device_t* device = NULL;
// status flag
tobii_error_t result = tobii_api_create(&api, NULL, NULL);
// the temporary record to update in the callbacks
Record tmp_record;
// camera object
cv::VideoCapture cap;
// images directory 
std::string user_images_path;
std::deque<cv::Mat> Frames;
std::deque<cv::Mat> all_frames(3);
int frame_width = 0;
int frame_height = 0;
cv::VideoWriter video;  


void save_to_file(int frame_id) {
    // save current image frame as image-{frame_id}.png
    if (!user_images_path.empty()) {
        std::string filename = user_images_path + "\\frame-" + std::to_string(frame_id) + ".png";
        if (!Frames[frame_id].empty()) {
            cv::imwrite(filename, Frames[frame_id]);
        }        
    }
    
}
// the tobii callbacks
void gaze_point_callback(tobii_gaze_point_t const* gaze_point, void* /* user_data */) {
    tmp_record.selfie_time = timeInMilliseconds();
    tmp_record.setGaze(gaze_point);
    cv::Mat f;
    if(cap.isOpened()){
        cap >> f;
        all_frames.push_back(f);
    }
    
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

bool assert_tobii_error(tobii_error_t result, const char* msg = "error"){
    if (result != TOBII_ERROR_NO_ERROR) {
        printf("%s % \n", tobii_error_message(result), msg);
        return true;
    }
    return false;
}

int start(int cam_index, char* images_path) {
    // set the images directory 
    user_images_path = images_path;
    if(!cap.open(cam_index)){
        printf("Error: Camera error \n");
    }
    else {
        frame_width = cap.get(cv::CAP_PROP_FRAME_WIDTH);
        frame_height = cap.get(cv::CAP_PROP_FRAME_HEIGHT);
        video = cv::VideoWriter(user_images_path + "/avi-video.avi", cv::VideoWriter::fourcc('M', 'J', 'P', 'G'), 10, cv::Size(frame_width, frame_height), true);
    }

    if (assert_tobii_error(result))
        return -1;

    // Enumerate devices to find connected eye trackers, keep the first
    char url[256] = { 0 };
    result = tobii_enumerate_local_device_urls(api, url_receiver, url);

    if (assert_tobii_error(result))
          return -1;

    if (*url == '\0'){
        printf("Error: No device found\n");
        return -1;
    }

    result = tobii_device_create(api, url, TOBII_FIELD_OF_USE_INTERACTIVE, &device);

    if (assert_tobii_error(result, "device"))
          return -1;

    // Subscribe to gaze data
    result = tobii_gaze_point_subscribe(device, gaze_point_callback, 0);
    result = tobii_gaze_origin_subscribe(device, gaze_origin_callback, 0);
    result = tobii_eye_position_normalized_subscribe(device, eye_position_callback, 0);

    if (assert_tobii_error(result, "subscription"))
          return -1;

    if (!updating) {
        updating = true;
        update_thread = std::thread(updateRecords);
    }
    update_thread.joinable();
    return 1;
}


int stop() {
    std::deque<std::thread> threads;
    if (updating) {
        updating = false;
        update_thread.join();
        for (int i = 0; i < Frames.size(); i ++) {
            threads.push_back(std::thread(save_to_file, i));
        }
        printf("saving images \n");
    }

    if (cap.isOpened()) {
        cap.release();
    }

    for (int i = 0; i < threads.size(); ++i) {
        threads[i].join();
    }
    printf("saved  %Ii images \n", Frames.size());
    // Cleanup
    if (device != NULL) {
        result = tobii_gaze_point_unsubscribe(device);
        if (assert_tobii_error(result, "unsubscription"))
            return result;

        result = tobii_device_destroy(device);
        if (assert_tobii_error(result, "dev destroy "))
            return result;
    }       
    if (api != NULL) {
        result = tobii_api_destroy(api);
        if (assert_tobii_error(result, "api destroy "))
            return result;
    }
    return 0;
}

Record* get_latest(int f_id) {   
    if (!all_frames.empty()) {
        Frames.push_back(all_frames.back());
        video.write(all_frames.back());
    }    
    return &tmp_record;
}

Record* get_records(int frame_id) {
    return &tmp_record;
}