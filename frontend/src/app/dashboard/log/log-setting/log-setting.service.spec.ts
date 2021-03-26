import { Apollo } from 'apollo-angular';
import { TestBed, inject } from '@angular/core/testing';

import { LogSettingService } from './log-setting.service';

describe('Service: LogSetting', () => {
  let serviceStub: Partial<Apollo>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: Apollo,
          useValue: serviceStub
        }
      ]
    });
  });

  it('should ...', inject([LogSettingService], (service: LogSettingService) => {
    expect(service).toBeTruthy();
  }));
});
