import multiprocessing as mproc


class MpFrameProcess(mproc.Process):

    def __init__(self, color_queue, depth_queue, stop_queue, intrinsics):
        super().__init__()

        # Queues creation:
        self.color_queue = color_queue
        self.depth_queue = depth_queue
        self.stop_queue = stop_queue
        self.depth_intrin_dict = intrinsics
        # print('Queues are in secondary process')


    def run(self):
        # 4. import libraries that use multiprocessing:
        import mediapipe as mp
        import numpy as np
        import pandas as pd
        import config_functions as cf
        import pyrealsense2 as rs
        import cv2

        n = 0

        print('Frames proc. Started')

        # Create a pose estimator here
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            min_tracking_confidence=0.5,
            min_detection_confidence=0.5,
            smooth_landmarks=False,
        )
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles

        depth_intrin = rs.pyrealsense2.intrinsics()

        depth_intrin.width = self.depth_intrin_dict['width']
        depth_intrin.height = self.depth_intrin_dict['height']
        depth_intrin.ppx = self.depth_intrin_dict['ppx']
        depth_intrin.ppy = self.depth_intrin_dict['ppy']
        depth_intrin.fx = self.depth_intrin_dict['fx']
        depth_intrin.fy = self.depth_intrin_dict['fy']
        depth_intrin.model = self.depth_intrin_dict['model']
        depth_intrin.coeffs = self.depth_intrin_dict['coeffs']

        final_landmarks = None

        while True:
            try:
                if not self.color_queue.empty():
                    color_image = self.color_queue.get()
                    depth_image = self.depth_queue.get()

                    if n == 0:
                        output, video_file_path = cf.create_video()

                    if color_image is None:  # Si recibe la señal de término, rompe el bucle
                        print('All frames processed')
                        self.stop_queue.put(True)
                        break

                    n += 1

                    results = pose.process(cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB))
                    landmarks_list = []

                    if not results.pose_landmarks:
                        print('NO LANDMARKS')
                        landmarks_list = np.zeros((1, 33 * 3))

                    else:
                        landmarks = results.pose_landmarks.landmark
                        for lmark in landmarks:
                            # lmark = landmarks[lm]

                            if 0 <= lmark.x < 0.9992 and 0 <= lmark.y < 0.9989:
                                pos_x = round(lmark.x * color_image.shape[1])
                                pos_y = round(lmark.y * color_image.shape[0])
                            else:
                                pos_x = 0
                                pos_y = 0
                            x, y, z = rs.rs2_deproject_pixel_to_point(depth_intrin, [pos_x, pos_y],
                                                                      depth_image[pos_y, pos_x])
                            landmarks_list.append(np.array([x, y, z]))

                            # landmarks_list.append(np.array([pos_x, pos_y, 34]))

                        landmarks_list = np.array(landmarks_list).flatten()

                    if final_landmarks is None:
                        final_landmarks = landmarks_list
                    else:
                        final_landmarks = np.vstack((final_landmarks, landmarks_list))

                    mp_drawing.draw_landmarks(
                        color_image,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing_styles
                        .get_default_pose_landmarks_style())

                    output.write(cv2.flip(color_image, 1))

            except BrokenPipeError:  # Handle broken pipe error (e.g., log, exit gracefully)
                break

        if final_landmarks is None:
            print('No landmarks to save')
            return

        landmark_file_path, number = cf.get_available_filename("landmarks/landmark_csv", "csv")

        # Convierte la lista de arrays en un DataFrame
        df = pd.DataFrame(final_landmarks)

        # Crear nombres de columna dinámicamente
        num_landmarks = len(final_landmarks[0]) // 3
        column_names = []
        for i in range(num_landmarks):
            lm_name = cf.get_landmark_name(i)
            column_names.extend([f'x_{i}_{lm_name}', f'y_{i}_{lm_name}', f'z_{i}_{lm_name}'])

        df.columns = column_names

        # Guarda el DataFrame como un archivo CSV
        df.to_csv(landmark_file_path, index=False)
        print('Landmarks saved to ', landmark_file_path)

        if output:
            output.release()
        print('Video saved to ', video_file_path)

