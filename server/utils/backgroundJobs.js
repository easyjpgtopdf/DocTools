/**
 * Background Job Queue
 * Handles background processing for long-running operations like OCR
 */

const EventEmitter = require('events');

class JobQueue extends EventEmitter {
  constructor() {
    super();
    this.queue = [];
    this.processing = false;
    this.maxConcurrent = 3; // Max 3 concurrent jobs
    this.activeJobs = 0;
    this.jobs = new Map(); // jobId -> job data
  }

  /**
   * Add job to queue
   */
  enqueue(job) {
    const jobId = job.id || `job-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const jobData = {
      id: jobId,
      ...job,
      status: 'queued',
      createdAt: new Date().toISOString()
    };
    
    this.jobs.set(jobId, jobData);
    this.queue.push(jobData);
    
    this.processQueue();
    
    return jobId;
  }

  /**
   * Process queue
   */
  async processQueue() {
    if (this.processing || this.activeJobs >= this.maxConcurrent) {
      return;
    }

    if (this.queue.length === 0) {
      return;
    }

    this.processing = true;

    while (this.queue.length > 0 && this.activeJobs < this.maxConcurrent) {
      const job = this.queue.shift();
      this.activeJobs++;
      
      this.processJob(job).catch(error => {
        console.error('Job processing error:', error);
        this.updateJobStatus(job.id, 'failed', { error: error.message });
      }).finally(() => {
        this.activeJobs--;
        this.processQueue();
      });
    }

    this.processing = false;
  }

  /**
   * Process a single job
   */
  async processJob(job) {
    this.updateJobStatus(job.id, 'processing');
    
    try {
      const result = await job.handler(job.data);
      this.updateJobStatus(job.id, 'completed', { result });
      this.emit('job:completed', job.id, result);
    } catch (error) {
      this.updateJobStatus(job.id, 'failed', { error: error.message });
      this.emit('job:failed', job.id, error);
      throw error;
    }
  }

  /**
   * Update job status
   */
  updateJobStatus(jobId, status, data = {}) {
    const job = this.jobs.get(jobId);
    if (job) {
      job.status = status;
      job.updatedAt = new Date().toISOString();
      Object.assign(job, data);
      this.jobs.set(jobId, job);
    }
  }

  /**
   * Get job status
   */
  getJobStatus(jobId) {
    return this.jobs.get(jobId);
  }

  /**
   * Cancel job
   */
  cancelJob(jobId) {
    const job = this.jobs.get(jobId);
    if (job && job.status === 'queued') {
      const index = this.queue.findIndex(j => j.id === jobId);
      if (index > -1) {
        this.queue.splice(index, 1);
      }
      this.updateJobStatus(jobId, 'cancelled');
      return true;
    }
    return false;
  }

  /**
   * Get queue stats
   */
  getStats() {
    return {
      queued: this.queue.length,
      active: this.activeJobs,
      total: this.jobs.size,
      completed: Array.from(this.jobs.values()).filter(j => j.status === 'completed').length,
      failed: Array.from(this.jobs.values()).filter(j => j.status === 'failed').length
    };
  }
}

// Global job queue instance
const jobQueue = new JobQueue();

module.exports = jobQueue;

