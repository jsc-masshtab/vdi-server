import { NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { VmDetailsComponent } from './vm-details.component';
import { VmsService } from '../all-vms/vms.service';

describe('VmDetailsComponent', () => {
  let component: VmDetailsComponent;
  let fixture: ComponentFixture<VmDetailsComponent>;

  let serviceStub: Partial<VmsService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getVm(): any {
        return {
          valueChanges: of({
            data: {
              vm: {}
            }
          })
        };
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ VmDetailsComponent ],
      providers: [
        {
          provide: VmsService,
          useValue: serviceStub
        },
        {
          provide: MatDialog,
          useValue: {}
        },
      ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VmDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
