import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed, inject } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { LicenseService } from './license.service';

describe('Service: License', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        RouterTestingModule
      ],
      providers: [ LicenseService ]
    });
  });

  it('should ...', inject([LicenseService], (service: LicenseService) => {
    expect(service).toBeTruthy();
  }));
});
