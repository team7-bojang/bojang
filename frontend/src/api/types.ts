export interface ApiSuccess<T> {
  success: true;
  data: T;
  timestamp?: string;
  request_id?: string;
}

export interface ApiFailure {
  success: false;
  error: {
    code: string;
    message: string;
  };
  timestamp?: string;
  request_id?: string;
}

export type ApiEnvelope<T> = ApiSuccess<T> | ApiFailure;
