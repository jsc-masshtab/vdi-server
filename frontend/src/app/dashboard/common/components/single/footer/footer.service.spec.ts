/* tslint:disable:no-unused-variable */

import { TestBed, async, inject } from '@angular/core/testing';
import { FooterService } from './footer.service';

describe('Service: Footer', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [FooterService]
    });
  });

  it('should ...', inject([FooterService], (service: FooterService) => {
    expect(service).toBeTruthy();
  }));
});
