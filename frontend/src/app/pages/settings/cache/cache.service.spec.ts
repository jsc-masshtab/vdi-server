import { TestBed, inject } from '@angular/core/testing';
import { Apollo } from 'apollo-angular';

import { CacheService } from './cache.service';

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

  it('should ...', inject([CacheService], (service: CacheService) => {
    expect(service).toBeTruthy();
  }));
});
