<?php
header('Content-Type: application/json; charset=utf-8');

$validToken = 'Bearer default_secure_token_123';
$headers = getallheaders();
$authHeader = $headers['Authorization'] ?? '';

if ($authHeader !== $validToken) {
    http_response_code(403);
    echo json_encode(['status' => 'error', 'message' => 'Unauthorized']);
    exit;
}

$action = $_REQUEST['action'] ?? $_POST['action'] ?? 'fetch';

if ($action === 'fetch') {
    $jobId = rand(1000, 9999);
    echo json_encode([
        'status' => 'success',
        'job_id' => $jobId,
        'transport_preference' => 'auto', 
        'printer_ip' => '192.168.1.100',
        'printer_port' => 9100,
        'windows_printer_name' => 'POS-80C', 
        'paper_width' => 42,
        'payload_type' => 'escpos',
        'content' => base64_encode("\x1b\x40Hello World!\n\x1b\x64\x05") 
    ]);
    exit;
}

if ($action === 'ack') {
    $jobId = (int)($_POST['job_id'] ?? 0);
    if ($jobId > 0) {
        echo json_encode(['status' => 'success', 'message' => "Job {$jobId} marked as printed"]);
    } else {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Invalid Job ID']);
    }
    exit;
}

if ($action === 'fail') {
    $jobId = (int)($_POST['job_id'] ?? 0);
    $reason = $_POST['reason'] ?? 'Unknown error';
    echo json_encode(['status' => 'success', 'message' => "Job {$jobId} moved to dead-letter queue. Reason: {$reason}"]);
    exit;
}

http_response_code(400);
echo json_encode(['status' => 'error', 'message' => 'Unknown action']);