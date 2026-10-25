export interface TranscriptItem {
  id: string;
  speaker: '상담사' | '민원인' | '혼합/식별중';
  text: string;
  raw_text?: string;
  is_final: boolean;
  confidence: number;
  start_time: number;
  end_time: number;
  timestamp_str: string;
  edited_by_counselor: boolean;
}

export interface RealtimeAnalysis {
  counseling_category: string;
  core_intent: string;
  current_summary: string;
  objective_facts: string[];
  caller_claims: string[];
  recommended_questions: string[];
  recommended_response_script: string;
  responsible_agency: string;
  caution_notes: string[];
  escalation_needed: string;
  escalation_reason?: string;
}

export interface FinalSummary {
  session_id: string;
  counselor_id: string;
  category: string;
  caller_intent: string;
  consultation_summary: string;
  action_taken: string;
  next_steps: string[];
  related_agency: string;
  escalation_status: string;
  raw_transcript_count: number;
  created_at: string;
}

export interface SessionSnapshot {
  session_id: string;
  counselor_id: string;
  counselor_name: string;
  start_time: string;
  recording_state: 'IDLE' | 'RECORDING' | 'PAUSED' | 'COMPLETED';
  interim_text: string;
  transcripts: TranscriptItem[];
  latest_analysis: RealtimeAnalysis;
  final_summary?: FinalSummary | null;
  transcript_count: number;
}

export interface AudioDevice {
  index: number;
  name: string;
  host_api: string;
  max_input_channels: number;
  default_samplerate: number;
  is_default: boolean;
  is_line_in_candidate: boolean;
  supported_sample_rates: number[];
}
