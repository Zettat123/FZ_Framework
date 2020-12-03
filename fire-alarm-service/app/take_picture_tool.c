#include <asm/types.h>
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <getopt.h>
#include <linux/videodev2.h>
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>

struct buffer {
  void *start;
  size_t length;
};

struct buffer *buffers;
unsigned long n_buffers;
unsigned long file_length;

int fd;
char *dev_name = "/dev/video0";
int file_fd;
char *picture_path = "1.jpg";

static int read_frame(void) {
  struct v4l2_buffer buf;

  buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  buf.memory = V4L2_MEMORY_MMAP;

  ioctl(fd, VIDIOC_DQBUF, &buf);

  if (buf.index > 2) return 0;
  write(file_fd, buffers[buf.index].start, buffers[buf.index].length);

  ioctl(fd, VIDIOC_QBUF, &buf);

  return 1;
}

int main(int argc, char **argv) {
  int width = 1280, height = 720;
  if (argc > 1) width = atoi(argv[1]);
  if (argc > 2) height = atoi(argv[2]);
  if (argc > 3) picture_path = argv[3];
  if (argc > 4) dev_name = argv[4];

  struct v4l2_capability cap;

  struct v4l2_format fmt;

  struct v4l2_requestbuffers req;

  struct v4l2_buffer buf;

  unsigned int i;
  enum v4l2_buf_type type;

  file_fd = open(picture_path, O_RDWR | O_CREAT, 0777);

  fd = open(dev_name, O_RDWR | O_NONBLOCK, 0);

  ioctl(fd, VIDIOC_QUERYCAP, &cap);
  printf("Driver Name:%s\nCard Name:%s\nBus info:%s\n\n", cap.driver, cap.card,
         cap.bus_info);

  fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  fmt.fmt.pix.width = width;
  fmt.fmt.pix.height = height;

  fmt.fmt.pix.field = V4L2_FIELD_INTERLACED;

  fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_MJPEG;

  ioctl(fd, VIDIOC_S_FMT, &fmt);

  req.count = 16;
  req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  req.memory = V4L2_MEMORY_MMAP;
  ioctl(fd, VIDIOC_REQBUFS, &req);

  printf("req.count = %d\n", req.count);

  buffers = calloc(req.count, sizeof(*buffers));

  for (n_buffers = 0; n_buffers < req.count; ++n_buffers) {
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buf.memory = V4L2_MEMORY_MMAP;
    buf.index = n_buffers;

    ioctl(fd, VIDIOC_QUERYBUF, &buf);

    buffers[n_buffers].length = buf.length;

    buffers[n_buffers].start = mmap(NULL, buf.length, PROT_READ | PROT_WRITE,
                                    MAP_SHARED, fd, buf.m.offset);
  }

  for (i = 0; i < n_buffers; ++i) {
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buf.memory = V4L2_MEMORY_MMAP;
    buf.index = i;
    ioctl(fd, VIDIOC_QBUF, &buf);
  }

  type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

  ioctl(fd, VIDIOC_STREAMON, &type);

  fd_set fds;

  FD_ZERO(&fds);

  FD_SET(fd, &fds);

  select(fd + 1, &fds, NULL, NULL, NULL);

  read_frame();

  for (i = 0; i < n_buffers; ++i) munmap(buffers[i].start, buffers[i].length);

  close(fd);
  close(file_fd);
  printf("Camera Done.\n");

  return 0;
}