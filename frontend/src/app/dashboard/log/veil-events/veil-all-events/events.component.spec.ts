import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { VeilEventsComponent } from './events.component';
import { VeilEventsService } from './events.service';

describe('EventsComponent', () => {
  let component: VeilEventsComponent;
  let fixture: ComponentFixture<VeilEventsComponent>;

  let serviceStub: Partial<VeilEventsService>;
  let dialogStub: Partial<MatDialog>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getAllEvents(): any {
        return {
          valueChanges: of({
            data: {
              events: [],
              entity_types: [],
              count: 1
            }
          })
        }
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [VeilEventsComponent ],
      providers: [
        {
          provide: MatDialog,
          useValue: dialogStub
        },
        {
          provide: VeilEventsService,
          useValue: serviceStub
        }
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VeilEventsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
