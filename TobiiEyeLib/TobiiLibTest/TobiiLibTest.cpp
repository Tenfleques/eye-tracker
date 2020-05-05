#include <iostream>
#include <opencv2/highgui.hpp>
#include <chrono>
#include <thread>
#include <deque>
#include <utility>


double timeInSeconds() {
    auto current_time = std::chrono::system_clock::now();
    auto duration_in_seconds = std::chrono::duration<double>(current_time.time_since_epoch());
    return duration_in_seconds.count();
}

std::string process_inject(std::string inject) {
    if (!inject.empty()) {
        if (!inject[0] == ',') {
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
        ss << "{\"x\": " << std::fixed << x << ", \"y\": " << std::fixed << y << process_inject(inject) << "}";
        return ss.str();
    }
    float x = .0, y = .0;
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
        ss << "{\"x\": " << std::fixed << x << ", \"y\": " << std::fixed << y << ", \"z\": " << z << process_inject(inject) << "}";
        return ss.str();
    }
    float z;
};
struct Gaze : Point2D {
    bool valid;
    double timestamp;
    Gaze() : valid(false), timestamp(.0) {};
    Gaze(const float l[2], bool v) {
        valid = v;
        timestamp = timeInSeconds();
        this->setXY(l[0], l[1]);
    }
    std::string to_json() {
        std::stringstream ss;
        ss << "\"valid\": " << valid << "\"timestamp\": " << std::fixed << timestamp;
        return to_string(ss.str());
    }
};
struct Eyes {
    Eyes(Point3D l, Point3D r) : left(std::move(l)), right(std::move(r)) {};
    Eyes(const float l[3], const float r[3]) : left(Point3D(l)), right(Point3D(r)) {};
    Eyes() : left(Point3D()), right(Point3D()) {};

    void setLeft(Point3D l) {
        left = std::move(l);
    }
    void setRight(Point3D r) {
        right = std::move(r);
    }
    Point3D left, right;
};
struct Pos3D : Eyes {
    double timestamp;
    bool valid;
    Pos3D() : valid(false), timestamp(.0) {};
    Pos3D(const float l[3], const float r[3], bool v) {
        valid = v;
        timestamp = timeInSeconds();
        this->setLeft(Point3D(l));
        this->setRight(Point3D(r));
    }
    std::string to_json() {
        std::stringstream ss;
        ss << "{\"valid\": " << valid << "\"timestamp\": " << std::fixed << timestamp
            << ", \"left\": " << left.to_string("")
            << "\"right\": " << right.to_string("") << "}";
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

    void update(Gaze& g) {
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
    void update(const char* path = nullptr) {
        cv::VideoCapture cap;
        if (path != nullptr) {
            cap = cv::VideoCapture(path);
            if (!cap.isOpened()) {
                std::cerr << "failed to open video " << path << std::endl;
                return;
            }
        }

        long counter = 0;
        std::cout << "preparing video" << std::endl;
        while (cap.isOpened()) {
            cv::Mat img;
            cap >> img;
            if (img.empty()) {
                break;
            }
            this->update(Frame(img, counter));
            counter++;
        }
        std::cout << "prepared " << counter << " frames " << " done." << std::endl;
        cap.release();
    }
    void update(Pos3D& pg, bool is_pos = true) {
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
    cv::Mat getFrameAt(long index) {
        if (video_frames.size() > index) {
            return video_frames[index].frame;
        }
        cv::Mat img;
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
        json += "{\"frames\": " + v_frames;
        json += ",\"camera\": " + c_frames;

        json += ",\"pos\": " + pos_frames;
        json += ",\"origin\": " + origin_frames;
        json += ",\"gaze\": " + gaze_frames;

        json += "}";
        return json;
    }
    [[nodiscard]] bool break_out_updates() const {
        return stop_updates;
    }
}sessionRecord;

void start(const char* path = nullptr, int delay = -1) {
    cv::VideoCapture cap;
    std::string win_name = "cam feed";
    if (path != nullptr) {
        sessionRecord.update(path);
        cv::namedWindow(win_name);
        if (delay == -1) {
            // need to get the video fps
            cap = cv::VideoCapture(path);
            double fps = cap.get(cv::CAP_PROP_FPS);
            delay = (int)(1000 / fps);
            std::cout << "using the fps of " << fps << " delaying for next frame by "
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
    }

    long counter = 0;
    double st = timeInSeconds();
    cv::Mat img;
    std::cout << sessionRecord.break_out_updates();
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
        }
        counter += 1;
    }

    double time_diff = timeInSeconds() - st;
    if (time_diff != 0) {
        std::cout << "after " << time_diff << " seconds, factual fps: " << (double)counter / (time_diff) << std::endl;
    }
    cap.release();
    sessionRecord.stop_updates = true;
    if (path != nullptr) {
        cv::destroyWindow(win_name);
    }
}

SessionRecord* get_records() {
    return &sessionRecord;
}

int main() {
    //    char * dir = _strdup("sample/images"); Windows
    //    char * dir = strdup("sample/images");
    //    std::thread cam_thread(start, nullptr, 1);
    start("./data/stimulus_sample.mp4", -1);
    //    cam_thread.join();
    std::cout << sessionRecord.to_json();
    int close;

    std::cin >> close;
    
    return 0;
}