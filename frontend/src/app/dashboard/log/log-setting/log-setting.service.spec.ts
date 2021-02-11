/* tslint:disable:no-unused-variable */

import { TestBed, async, inject } from '@angular/core/testing';
import { LogSettingService } from './log-setting.service';

describe('Service: LogSetting', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [LogSettingService]
    });
  });

  it('should ...', inject([LogSettingService], (service: LogSettingService) => {
    expect(service).toBeTruthy();
  }));
});
