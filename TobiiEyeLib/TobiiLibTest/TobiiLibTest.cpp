#include <tobii/tobii.h>
#include <tobii/tobii_streams.h>
#include <stdio.h>
#include <assert.h>
#include <limits.h>

#include <iostream>
#include <opencv2/highgui.hpp>
#include <chrono>
#include <thread>
#include <deque>
#include <utility>
#include <fstream>


double timeInSeconds() {
    auto current_time = std::chrono::system_clock::now();
    auto duration_in_seconds = std::chrono::duration<double>(current_time.time_since_epoch());
    return duration_in_seconds.count();
}

std::string process_inject(std::string inject) {
    if (!inject.empty()) {
        if (!inject.front() == ',') {
            inject = "," + inject;
        }
    }
    return inject;
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
    void setXY(const float xx, const float yy) {
        y = yy;
        x = xx;
    }

    virtual std::string to_string(const std::string& inject) {
        std::stringstream ss;
        ss << "{\"x\": " << std::fixed << x
            << ",\"y\": " << std::fixed << y << process_inject(inject) << "}";
        return ss.str();
    }
    float x = .0, y = .0;
};

struct Gaze : Point2D {
    bool valid;
    double timestamp;
    int64_t timestamp_us = 0;

    Gaze() : valid(false), timestamp(.0) {};
    Gaze(const float l[2], bool v, int64_t t) {
        valid = v;
        timestamp = timeInSeconds();
        timestamp_us = t;
        this->setXY(l[0], l[1]);
    }
    Gaze(const float l, const float r, bool v, int64_t t) {
        valid = v;
        timestamp = timeInSeconds();
        timestamp_us = t;
        this->setXY(l, r);
    }
    std::string to_json() {
        std::stringstream ss;
        ss << "\"valid\": " << valid << ",\"timestamp_us\": " << timestamp_us
            << ",\"timestamp\": " << std::fixed << timestamp;
        return to_string(ss.str());
    }
};

struct Point3D : Point2D {
    Point3D(const float x, const float y, const float zz) {
        z = zz;
        this->setX(x);
        this->setY(y);
    };
    explicit Point3D(const float l[3]) {
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
    void setXYZ(const float xx, const float yy, const float zz) {
        y = yy;
        x = xx;
        z = zz;
    }
    std::string to_string(const std::string& inject) override {
        std::stringstream ss;
        ss << "{\"x\": " << std::fixed << x << ", \"y\": "
            << std::fixed << y << ", \"z\": " << z << process_inject(inject) << "}";
        return ss.str();
    }
    float z;
};
struct Eyes {
    Eyes(Point3D l, Point3D r) : left(std::move(l)), right(std::move(r)) {};
    Eyes(const float l[3], const float r[3]) : left(Point3D(l)), right(Point3D(r)) {};
    Eyes() : left(Point3D()), right(Point3D()) {};

    void setLeft(Point3D l, bool v) {
        left = std::move(l);
        v_l = v;
    }
    void setRight(Point3D r, bool v) {
        right = std::move(r);
        v_r = v;
    }
    Point3D left, right;
    bool v_l = false, v_r = false;
};
struct Pos3D : Eyes {
    double timestamp;
    int64_t timestamp_us = 0;

    Pos3D() : timestamp(.0) {};
    Pos3D(const float l[3], const float r[3], const bool v[2], const int64_t t) {
        timestamp = timeInSeconds();
        timestamp_us = t;
        this->setLeft(Point3D(l), v[0]);
        this->setRight(Point3D(r), v[1]);
    }
    std::string to_json() {
        std::stringstream ss;
        std::stringstream sv_l;
        std::stringstream sv_r;
        sv_l << "\"valid\": " << v_l;

        sv_r << "\"valid\": " << v_r;

        ss << "{\"timestamp\": " << std::fixed << timestamp
            << ",\"timestamp_us\": " << timestamp_us
            << ",\"left\": " << left.to_string(sv_l.str())
            << ",\"right\": " << right.to_string(sv_r.str()) << "}";
        return ss.str();
    }
};
struct Frame {
    long id;
    double timestamp;
    cv::Mat frame;
    Frame(cv::Mat  f, long i) : frame(std::move(f)), id(i), timestamp(timeInSeconds()) {};
    Frame() :id(0), timestamp(timeInSeconds()) {};
    explicit Frame(long i) :id(i), timestamp(timeInSeconds()) {};
    Frame(long i, double t) :id(i), timestamp(t) {};

    void update_timestamp() {
        timestamp = timeInSeconds();
    }

    bool save_to_file(const std::string user_images_path) {
        // save current image frame as image-{frame_id}.png
        if (!user_images_path.empty()) {
            std::string filename = user_images_path + "\\frame-" + std::to_string(id) + ".png";
            if (!frame.empty()) {
                return cv::imwrite(filename, frame);
            }
        }
        return false;
    }


    [[nodiscard]] std::string to_json() const {
        std::stringstream ss;
        ss << "{\"id\": " << std::fixed << id << "\"timestamp\": " << std::fixed << timestamp << "}";
        return ss.str();
    }
};

struct SessionRecord {
    std::deque<Frame> camera_frames;
    std::deque<Frame> video_frames;
    std::deque<Gaze> gazes;
    std::deque<Pos3D> poses;
    std::deque<Pos3D> origins;
    bool stop_updates = false;
    bool record_tracker = false;

    ~SessionRecord() {
        camera_frames.~deque();
        video_frames.~deque();
        gazes.~deque();
        poses.~deque();
        origins.~deque();

    }
    void update(Gaze g) {
        if (!this->is_recording_tracker())
            return;
        gazes.push_back(g);
    }
    void update(const Frame& f, bool is_cam_frame = false) {
        if (is_cam_frame) {
            camera_frames.push_back(f);
        }
        else {
            video_frames.push_back(f);
        }
    }
    int update(const char* path = nullptr) {
        if (path != nullptr) {
            cv::VideoCapture cap(path);
            if (!cap.isOpened()) {
                std::cerr << "[ERROR] failed to open video " << path << std::endl;
                return -1;
            }
            long counter = 0;
            std::cout << "[INFO] preparing video ... " << std::endl;
            while (cap.isOpened()) {
                cv::Mat img;
                cap >> img;
                if (img.empty()) {
                    break;
                }
                this->update(Frame(img, counter));
                counter++;
            }
            std::cout << "[INFO] prepared " << counter << " frames " << " done." << std::endl;
            cap.release();
        }

        return 0;
    }
    void update(Pos3D pg, bool is_pos = true) {
        if (!this->is_recording_tracker())
            return;

        if (is_pos) {
            poses.push_back(pg);
        }
        else {
            origins.push_back(pg);
        }
    }
    void update(long index) {
        if (video_frames.size() > index) {
            video_frames[index].update_timestamp();
        }
    }
    long save_images(const std::string user_images_path) {
        long save_count = 0;
        for (auto f : camera_frames) {
            int saved = (int)f.save_to_file(user_images_path);
            save_count += saved;
        }
        return save_count - camera_frames.size();
    }
    cv::Mat getFrameAt(long index) {
        if (video_frames.size() > index) {
            return video_frames[index].frame;
        }
        cv::Mat img;
        return img;
    }
    cv::Mat popFrame() {
        cv::Mat img;
        if (video_frames.size() > 0) {
            img = video_frames[0].frame;
            video_frames.pop_front();
        }        
        return img;
    }
    static std::string frames_json(const std::deque<Frame>& f) {
        std::string frames;
        for (const auto& s : f) {
            if (frames.empty()) {
                frames += s.to_json();
            }
            else {
                frames += ", " + s.to_json();
            }
        }
        frames = "{" + frames + "}";
        return  frames;
    }
    static std::string pos3d_json(const std::deque<Pos3D>& f) {
        std::string frames;
        for (auto s : f) {
            if (frames.empty()) {
                frames += s.to_json();
            }
            else {
                frames += ", " + s.to_json();
            }
        }
        frames = "{" + frames + "}";
        return  frames;
    }
    static std::string g_json(const std::deque<Gaze>& f) {
        std::string frames;
        for (auto s : f) {
            if (frames.empty()) {
                frames += s.to_json();
            }
            else {
                frames += ", " + s.to_json();
            }
        }
        frames = "{" + frames + "}";
        return  frames;
    }
    [[nodiscard]] std::string to_json() const {
        std::string v_frames = frames_json(video_frames);
        std::string c_frames = frames_json(camera_frames);
        std::string pos_frames = pos3d_json(poses);
        std::string origin_frames = pos3d_json(origins);
        std::string gaze_frames = g_json(gazes);

        std::string json;
        json += "{\"frames\": [" + v_frames;
        json += "],\"camera\": [" + c_frames;
        json += "],\"pos\": [" + pos_frames;
        json += "],\"origin\" [: " + origin_frames;
        json += "],\"gaze\": [" + gaze_frames;
        json += "]}";
        return json;
    }
    [[nodiscard]] bool break_out_updates() const {
        return stop_updates;
    }
    [[nodiscard]] bool is_recording_tracker() const {
        return record_tracker;
    }
}sessionRecord;

// the tobii-tracker callbacks
void gaze_point_callback(tobii_gaze_point_t const* gaze_point, void* /* user_data */) {
    // update gaze
    sessionRecord.update(Gaze(gaze_point->position_xy,
        gaze_point->validity == TOBII_VALIDITY_VALID,
        gaze_point->timestamp_us));
}
void gaze_origin_callback(tobii_gaze_origin_t const* gaze_origin, void* user_data) {
    bool valid[2] = { gaze_origin->left_validity == TOBII_VALIDITY_VALID,
                     gaze_origin->right_validity == TOBII_VALIDITY_VALID };

    sessionRecord.update(Pos3D(gaze_origin->left_xyz,
        gaze_origin->right_xyz,
        valid, gaze_origin->timestamp_us), false);
}
void eye_position_callback(tobii_eye_position_normalized_t const* eye_pos, void* user_data) {
    bool valid[2] = { eye_pos->left_validity == TOBII_VALIDITY_VALID,
                     eye_pos->right_validity == TOBII_VALIDITY_VALID };

    sessionRecord.update(Pos3D(eye_pos->left_xyz,
        eye_pos->right_xyz,
        valid, eye_pos->timestamp_us), true);
}

bool assert_tobii_error(const tobii_error_t result, const char* msg = "error") {
    if (result != TOBII_ERROR_NO_ERROR) {
        std::cerr << "[ERROR] " << tobii_error_message(result) << " " << msg;
        return true;
    }
    return false;
}

void url_receiver(char const* url, void* user_data) {
    char* buffer = (char*)user_data;
    if (*buffer != '\0') return; // only keep first value

    std::string ur_s = url;
    const char* ur_ss = ur_s.c_str();

    if (strlen(url) < 256)
        strcpy(buffer, ur_ss);
}

struct tobiiCtrl {
    // Create API
    tobii_api_t* api = NULL;
    // Connect to the first tracker found
    tobii_device_t* device = NULL;
    // status flag
    tobii_error_t result = tobii_api_create(&api, NULL, NULL);
    // updates thread 

    void updateRecords() {
        while (!sessionRecord.break_out_updates()) {
            // Optionally block this thread until data is available. Especially useful if running in a separate thread.
            result = tobii_wait_for_callbacks(1, &device);
            assert(result == TOBII_ERROR_NO_ERROR || result == TOBII_ERROR_TIMED_OUT);

            // Process callbacks on this thread if data is available
            result = tobii_device_process_callbacks(device);
            assert(result == TOBII_ERROR_NO_ERROR);
        }
    }
    int start() {
        if (assert_tobii_error(result))
            return -1;

        // Enumerate devices to find connected eye trackers, keep the first
        char url[256] = { 0 };
        result = tobii_enumerate_local_device_urls(api, url_receiver, url);

        if (assert_tobii_error(result))
            return -1;

        if (*url == '\0') {
            std::cerr << "[ERROR] No device found\n";
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

        return 0;
    }

    int stop() {
        // Cleanup
        if (device != NULL) {
            result = tobii_gaze_point_unsubscribe(device);
            if (assert_tobii_error(result, "unsubscribed"))
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
}tobiiCtrl;

void tobii_thread() {
    tobiiCtrl.updateRecords();
}
void start(const char* path = nullptr, int delay = -1, const char* out_path = nullptr) {
    cv::VideoCapture cap;
    std::string win_name = "cam feed";
    std::string user_images_path;
    cv::VideoWriter video;
    std::thread update_thread;

    if (path != nullptr) {
        int video_ready = sessionRecord.update(path);
        win_name = path;
        // start recording from the tracker
        if (video_ready == 0) {
            cv::namedWindow(win_name);
            sessionRecord.record_tracker = true;
            int tobii_started = tobiiCtrl.start();
            if (tobii_started == 0) {
                update_thread = std::thread(tobii_thread);
                std::cout << "[INFO] tracker device initialised and returns status code : "
                    << tobii_started << std::endl;
            }
            else {
                std::cout << "[ERROR] tracker device failed to initialise and returns status code : "
                    << tobii_started << std::endl;
                sessionRecord.record_tracker = false;
                sessionRecord.stop_updates = true;
                cap.release();
                video.release();
                return;
            }
        }
        else {
            sessionRecord.record_tracker = false;
            sessionRecord.stop_updates = true;
            cap.release();
            video.release();
            return;
        }


        if (delay == -1) {
            // need to get the video fps
            cap = cv::VideoCapture(path);
            double fps = cap.get(cv::CAP_PROP_FPS);
            delay = (int)(1000 / fps);
            std::cout << "[INFO] using the fps of " << fps << " delaying for next frame by "
                << delay << " milliseconds " << std::endl;
        }
    }
    else {
        while (!cap.open(0)) {
            std::cerr << "failed to open cap" << std::endl;
            return;
        }
        if (delay == -1) {
            // user hasn't defined the wait time for the web-cam
            delay = 1;
        }
        // setup video writer
        if (out_path != nullptr) {
            user_images_path = std::string(out_path);
            const int frame_width = cap.get(cv::CAP_PROP_FRAME_WIDTH);
            const int frame_height = cap.get(cv::CAP_PROP_FRAME_HEIGHT);
            video = cv::VideoWriter(user_images_path + "/avi-video.avi",
                cv::VideoWriter::fourcc('M', 'J', 'P', 'G'), 10,
                cv::Size(frame_width, frame_height), true);
        }
    }

    long counter = 0;
    double st = timeInSeconds();
    cv::Mat img;
    while (!sessionRecord.break_out_updates()) {
        if (path != nullptr) {
            // video source is prepared file
            img = sessionRecord.getFrameAt(counter);
            if (img.empty()) {
                break;
            }
            cv::imshow(win_name, img);
            sessionRecord.update(counter);
            if (cv::waitKey(delay) == 27) {
                break;
            }
        }
        else {
            // video source is camera
            cap >> img;
            sessionRecord.update(Frame(img, counter), true);
            video.write(img);
        }
        counter += 1;
    }

    double time_diff = timeInSeconds() - st;
    if (time_diff != 0 && path != nullptr) {
        sessionRecord.record_tracker = false;
        sessionRecord.stop_updates = true;
        cv::destroyWindow(win_name);

        if (update_thread.joinable()) {
            update_thread.join();
        }
    }
    std::cout << "[INFO] after " << time_diff << " seconds, factual video fps: "
        << (double)counter / (time_diff) << std::endl;
    std::cout << "[INFO] tracker device stopped and returned code: " << tobiiCtrl.stop() << std::endl;
    cap.release();
    video.release();
}

// exports 

const char* get_json() {
    const char* res = sessionRecord.to_json().c_str();
    return res;
}

SessionRecord* get_session() {
    return &sessionRecord;
}

long save_images(const char* out_path = nullptr) {
    if (out_path == nullptr) {
        return -1;
    }
    std::string user_images_path = std::string(out_path);

    if (!user_images_path.empty()) {
        return sessionRecord.save_images(user_images_path);
    }
    return -1;
}

int run(const char* src_path = nullptr, const char* out_path = nullptr) {
    std::thread cam_thread(start, nullptr, 1, nullptr);
    start(src_path, -1, out_path);
    cam_thread.join();
    return 0;
}
int main(int argc, char* argv[]){

    std::string def_src = "./data/stimulus_sample.mp4";
    std::string def_out = "./data";
    
    if (argc == 3) {
        def_src = argv[1];
        def_out = argv[2];
       
    }
    std::string out_json = def_out;
    run(def_src.c_str(), def_out.c_str());

    std::ofstream f;
    f.open(out_json + "/results.json");
    f << sessionRecord.to_json();
    f.close();   

    std::cout << "INFO saving images" << std::endl;
    save_images(out_json.c_str());
    std::cout << "INFO saved images" << std::endl;
    exit(0);
    return 0;
}