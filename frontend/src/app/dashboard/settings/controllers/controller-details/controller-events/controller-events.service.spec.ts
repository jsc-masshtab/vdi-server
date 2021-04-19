/* tslint:disable:no-unused-variable */

import { TestBed, async, inject } from '@angular/core/testing';
import { ControllerEventsService } from './controller-events.service';

describe('Service: ControllerEvents', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ControllerEventsService]
    });
  });

  it('should ...', inject([ControllerEventsService], (service: ControllerEventsService) => {
    expect(service).toBeTruthy();
  }));
});
