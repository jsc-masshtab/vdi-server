/* tslint:disable:no-unused-variable */

import { TestBed, async, inject } from '@angular/core/testing';
import { LicenseService } from './license.service';

describe('Service: License', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [LicenseService]
    });
  });

  it('should ...', inject([LicenseService], (service: LicenseService) => {
    expect(service).toBeTruthy();
  }));
});
