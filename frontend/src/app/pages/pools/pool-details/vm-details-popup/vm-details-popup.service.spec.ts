/* tslint:disable:no-unused-variable */

import { TestBed, async, inject } from '@angular/core/testing';

import { VmDetailsPopupService } from './vm-details-popup.service';

describe('Service: VmDetailsPopup', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [VmDetailsPopupService]
    });
  });

  it('should ...', inject([VmDetailsPopupService], (service: VmDetailsPopupService) => {
    expect(service).toBeTruthy();
  }));
});
