import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { ControllerDetailsComponent } from './controller-details.component';
import { ControllersService } from './../all-controllers/controllers.service';

describe('ControllerDetailsComponent', () => {
  let component: ControllerDetailsComponent;
  let fixture: ComponentFixture<ControllerDetailsComponent>;

  let serviceStub: Partial<ControllersService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getController(): any {
        return of({
          data: {
            controller: {}
          }
        });
      }
    };

    TestBed.configureTestingModule({
      imports: [
        RouterTestingModule
      ],
      declarations: [ ControllerDetailsComponent ],
      providers: [
        {
          provide: ControllersService,
          useValue: serviceStub
        },
        {
          provide: MatDialog,
          useValue: {}
        },
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ControllerDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
