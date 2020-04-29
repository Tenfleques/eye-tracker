#include <iostream>
#include "TobiEyeLib.h"
#include <opencv2/opencv.hpp>
#include <chrono>
#include <windows.h>

using namespace std;

double timeInMilliseconds() {
    SYSTEMTIME tim;
    GetSystemTime(&tim);
    double time_ms = time(0) + tim.wMilliseconds / 1000.0;
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

    void setFrame(cv::Mat f) {
        frame = f;
        selfie_time = timeInMilliseconds();
        cv::Size s = f.size();
        img_shape = Point3D(s.height, s.width, 3);
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
    cv::Mat frame;
    Point3D img_shape;
};

void playVideo() {
    cv::VideoCapture cam;
    while (!cam.open(0))cerr << "failed to open cam" << endl;
    cv::namedWindow("test");
    
    while (1) {
        cv::Mat img;
        cam >> img;
        Record* tmp_record = get_latest(0);
        if (tmp_record->gaze_valid)
            tmp_record->print();

        cv::imshow("test", img);
        if (cv::waitKey(1) == 27)
            break;
    }
    cv::destroyWindow("test");
}
int main() {
    char * dir = _strdup("sample/images");
    cout << start(0, dir);
    playVideo();
    stop();
}

