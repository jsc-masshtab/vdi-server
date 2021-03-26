import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { ErrorsComponent } from './errors.component';
import { ErrorsService } from './errors.service';

describe('ErrorsComponent', () => {
  let component: ErrorsComponent;
  let fixture: ComponentFixture<ErrorsComponent>;

  let serviceStub: Partial<ErrorsService>;

  beforeEach(async(() => {
    serviceStub = {
      getErrors() {
        return of({});
      }
    };

    TestBed.configureTestingModule({
      declarations: [ ErrorsComponent ],
      providers: [
        {
          provide: ErrorsService,
          useValue: serviceStub
        }
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ErrorsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
