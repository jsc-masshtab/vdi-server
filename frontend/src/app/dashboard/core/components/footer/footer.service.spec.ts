import { TestBed, inject } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { FooterService } from './footer.service';

describe('Service: Footer', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        RouterTestingModule
      ],
      providers: [ FooterService ]
    });
  });

  it('should ...', inject([FooterService], (service: FooterService) => {
    expect(service).toBeTruthy();
  }));
});
