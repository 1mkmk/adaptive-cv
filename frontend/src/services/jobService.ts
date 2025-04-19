import { fetchApi } from './api';

export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  description: string;
  source_url?: string;
  created_at: string;
  cv?: string;
}

export interface JobCreateParams {
  title: string;
  company: string;
  location: string;
  description: string;
  requirements?: string;
  job_url?: string;
}

export async function getJobs(): Promise<Job[]> {
  try {
    return await fetchApi('/jobs');
  } catch (error) {
    console.error('Error fetching jobs:', error);
    return [];
  }
}

export async function getJob(id: number): Promise<Job | null> {
  try {
    return await fetchApi(`/jobs/${id}`);
  } catch (error) {
    console.error(`Error fetching job ${id}:`, error);
    return null;
  }
}

export async function createJob(jobData: JobCreateParams): Promise<Job | null> {
  try {
    // Convert to FormData since the backend uses Form for job creation
    const formData = new FormData();
    Object.entries(jobData).forEach(([key, value]) => {
      if (value !== undefined) {
        formData.append(key, value);
      }
    });

    return await fetchApi('/jobs/create', {
      method: 'POST',
      body: formData,
      headers: {
        // Let the browser set the content type for FormData
        'Accept': 'application/json',
      },
    });
  } catch (error) {
    console.error('Error creating job:', error);
    return null;
  }
}

export async function deleteJob(id: number): Promise<boolean> {
  try {
    await fetchApi(`/jobs/${id}`, {
      method: 'DELETE',
    });
    return true;
  } catch (error) {
    console.error(`Error deleting job ${id}:`, error);
    return false;
  }
}