export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
  timestamp?: string;
  request_id?: string;
}

export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
  };
  timestamp?: string;
  request_id?: string;
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;
