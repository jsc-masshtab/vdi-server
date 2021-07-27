import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { VmsComponent } from './vms.component';
import { VmsService } from './vms.service';

describe('VmsComponent', () => {
  let component: VmsComponent;
  let fixture: ComponentFixture<VmsComponent>;

  let serviceStub: Partial<VmsService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getAllVms(): any {
        return {
          valueChanges: of({
            data: {
              vms: []
            }
          })
        };
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ VmsComponent ],
      providers: [
        {
          provide: VmsService,
          useValue: serviceStub
        },
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VmsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
