import motmetrics as mm
import numpy as np

def evaluate_tracking(ground_truth_tracks, pipeline_tracks):
    """
    Computes standard MOTA/MOTP metrics.
    
    ground_truth_tracks: dict mapping frame_idx -> list of [obj_id, x1, y1, x2, y2]
    pipeline_tracks: dict mapping frame_idx -> list of [obj_id, x1, y1, x2, y2]
    """
    acc = mm.MOTAccumulator(auto_id=True)
    
    # Iterate through every frame to find spatial matches
    all_frames = sorted(list(set(ground_truth_tracks.keys()) | set(pipeline_tracks.keys())))
    
    for frame in all_frames:
        gt = ground_truth_tracks.get(frame, [])
        dt = pipeline_tracks.get(frame, [])
        
        gt_ids = [obj[0] for obj in gt]
        dt_ids = [obj[0] for obj in dt]
        
        # Calculate distance matrix based on bounding box centroids or IoU
        distances = []
        for g in gt:
            frame_dist = []
            g_cx, g_cy = (g[1]+g[3])/2, (g[2]+g[4])/2
            for d in dt:
                d_cx, d_cy = (d[1]+d[3])/2, (d[2]+d[4])/2
                # Euclidean distance between box centers
                dist = np.sqrt((g_cx - d_cx)**2 + (g_cy - d_cy)**2)
                frame_dist.append(dist)
            distances.append(frame_dist)
            
        # Clear distant pairings (threshold: 50 pixels matching constraint)
        distances = np.array(distances)
        if distances.size > 0:
            distances[distances > 50.0] = np.nan
            
        acc.update(gt_ids, dt_ids, distances.tolist())
        
    mh = mm.metrics.create()
    summary = mh.compute(acc, metrics=['num_frames', 'mota', 'motp', 'id_switches', 'num_false_positives'], name='YOLO_ByteTrack_Eval')
    print(mh.io.render_summary(summary, format='markdown'))

if __name__ == "__main__":
    print("MOT Evaluation Script Initialized.")
    # Example usage: evaluate_tracking(gt_dict, dt_dict)